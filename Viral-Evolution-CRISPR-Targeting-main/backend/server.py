from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Tuple
import uuid
from datetime import datetime
import io

# BioPython imports
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

# ML and analysis imports
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import re
import json

# Helper function to calculate GC content
def calculate_gc_content(sequence):
    """Calculate GC content as a percentage"""
    gc_count = sequence.count('G') + sequence.count('C')
    return (gc_count / len(sequence)) * 100 if len(sequence) > 0 else 0

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Viral Evolution CRISPR Targeting API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Pydantic Models
class ViralSequence(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    sequence: str
    virus_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CRISPRTarget(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sequence_id: str
    target_sequence: str
    pam_sequence: str
    position: int
    strand: str
    gc_content: float
    conservation_score: float
    escape_probability: float
    binding_strength: float

class AnalysisResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sequence_id: str
    total_targets: int
    high_confidence_targets: int
    conservation_data: Dict
    escape_analysis: Dict
    recommendations: List[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SequenceUpload(BaseModel):
    name: str
    sequence: str
    virus_type: str

class MutationSimulation(BaseModel):
    original_sequence: str
    mutation_rate: float = 0.001
    generations: int = 100

# CRISPR Analysis Engine
class CRISPRAnalyzer:
    def __init__(self):
        self.pam_pattern = r'[ATCG]GG'  # Cas9 PAM sequence (NGG)
        self.target_length = 20
        
    def find_pam_sites(self, sequence: str) -> List[Tuple[int, str]]:
        """Find all PAM sites in the sequence"""
        pam_sites = []
        for match in re.finditer(self.pam_pattern, sequence):
            pam_sites.append((match.start(), match.group()))
        return pam_sites
    
    def extract_target_sequences(self, sequence: str) -> List[Dict]:
        """Extract CRISPR target sequences around PAM sites"""
        targets = []
        pam_sites = self.find_pam_sites(sequence)
        
        for pam_pos, pam_seq in pam_sites:
            # Extract target sequence (20 bp upstream of PAM)
            if pam_pos >= self.target_length:
                target_start = pam_pos - self.target_length
                target_seq = sequence[target_start:pam_pos]
                
                if len(target_seq) == self.target_length:
                    targets.append({
                        'target_sequence': target_seq,
                        'pam_sequence': pam_seq,
                        'position': target_start,
                        'strand': '+',
                        'gc_content': calculate_gc_content(target_seq)
                    })
        
        # Check reverse complement
        rev_comp = str(Seq(sequence).reverse_complement())
        pam_sites_rev = self.find_pam_sites(rev_comp)
        
        for pam_pos, pam_seq in pam_sites_rev:
            if pam_pos >= self.target_length:
                target_start = pam_pos - self.target_length
                target_seq = rev_comp[target_start:pam_pos]
                
                if len(target_seq) == self.target_length:
                    # Convert back to original sequence coordinates
                    orig_pos = len(sequence) - pam_pos - 3
                    targets.append({
                        'target_sequence': target_seq,
                        'pam_sequence': pam_seq,
                        'position': orig_pos,
                        'strand': '-',
                        'gc_content': calculate_gc_content(target_seq)
                    })
        
        return targets
    
    def calculate_conservation_score(self, target_seq: str, variant_sequences: List[str]) -> float:
        """Calculate conservation score across viral variants"""
        if not variant_sequences:
            return 1.0
        
        conservation_scores = []
        for variant in variant_sequences:
            # Simple identity calculation
            if target_seq in variant:
                conservation_scores.append(1.0)
            else:
                # Calculate similarity
                matches = sum(1 for a, b in zip(target_seq, variant[:len(target_seq)]) if a == b)
                conservation_scores.append(matches / len(target_seq))
        
        return np.mean(conservation_scores)
    
    def predict_escape_probability(self, target_seq: str, gc_content: float, conservation_score: float) -> float:
        """Predict escape probability using simple heuristics"""
        # Higher GC content tends to be more stable
        gc_factor = 1.0 - abs(gc_content - 50) / 50
        
        # Higher conservation means lower escape probability
        conservation_factor = conservation_score
        
        # Simple escape probability calculation
        escape_prob = 1.0 - (gc_factor * 0.3 + conservation_factor * 0.7)
        return max(0.0, min(1.0, escape_prob))
    
    def calculate_binding_strength(self, target_seq: str) -> float:
        """Estimate CRISPR binding strength"""
        # Simple scoring based on sequence features
        gc_content = calculate_gc_content(target_seq)
        
        # Penalize extreme GC content
        gc_penalty = abs(gc_content - 50) / 50
        
        # Look for secondary structures (simplified)
        repeat_penalty = 0
        for i in range(len(target_seq) - 3):
            if target_seq[i:i+4] in target_seq[i+4:]:
                repeat_penalty += 0.1
        
        binding_strength = 1.0 - gc_penalty * 0.3 - repeat_penalty * 0.2
        return max(0.0, min(1.0, binding_strength))

# Initialize analyzer
crispr_analyzer = CRISPRAnalyzer()

# Sample viral sequences for testing
SAMPLE_SEQUENCES = {
    "HIV-1": "ATGGGTGCGAGAGCGTCAGTATTAAGCGGGGGAGAATTAGATCGATGGGAAAAAATTCGGTTAAGGCCAGGGGGAAAGAAAAAATATAAATTAAAACATATAGTATGGGCAAGCAGGGAGCTAGAACGATTCGCAGTTAATCCTGGCCTGTTAGAAACATCAGAAGGCTGTAGACAAATACTGGGACAGCTACAACCATCCCTTCAGACAGGATCAGAAGAACTTAGATCATTATATAATACAGTAGCAACCCTCTATTGTGTGCATCAAAGGATAGAGATAAAAGACACCAAGGAAGCTTTAGACAAGATAGAGGAAGAGCAAAACAAAAGTAAGAAAAAAGCACAGCAAGCAGCAGCTGACACAGGACACAGCAATCAGGTCAGCCAAAATTACCCTATAGTGCAGAACATCCAGGGGCAAATGGTACATCAGGCCATATCACCTAGAACTTTAAATGCATGGGTAAAAGTAGTAGAAGAGAAGGCTTTCAGCCCAGAAGTGATACCCATGTTTTCAGCATTATCAGAAGGAGCCACCCCACAAGATTTAAACACCATGCTAAACACAGTGGGGGGACATCAAGCAGCCATGCAAATGTTAAAAGAGACCATCAATGAGGAAGCTGCAGAATGGGATAGAGTGCATCCAGTGCATGCAGGGCCTATTGCACCAGGCCAGATGAGAGAACCAAGGGGAAGTGACATAGCAGGAACTACTAGTACCCTTCAGGAACAAATAGGATGGATGACAAATAATCCACCTATCCCAGTAGGAGAAATTTATAAAAGATGGATAATCCTGGGATTAAATAAAATAGTAAGAATGTATAGCCCTACCAGCATTCTGGACATAAGACAAGGACCAAAGGAACCCTTTAGAGACTATGTAGACCGGTTCTATAAAACTCTAAGAGCCGAGCAAGCTTCACAGGAGGTAAAAAATTGGATGACAGAAACCTTGTTGGTCCAAAATGCGAACCCAGATTGTAAGACTATTTTAAAAGCATTGGGACCAGGGGCTACACTAGAAGAAATGATGACAGCATGTCAGGGAGTAGGAGGACCCGGCCATAAAGCAAGAGTTTTGGCTGAAGCAATGAGCCAAGTAACAAATTCAGCTACCATAATGATGCAGAGAGGCAATTTTAGGAACCAAAGAAAGATTGTTAAGTGTTTCAATTGTGGCAAAGAAGGGCACACAGCCAGAAATTGCAGGGCCCCTAGGAAAAAGGGCTGTTGGAAATGTGGAAAGGAAGGACACCAAATGAAAGATTGTACTGAGAGACAGGCTAATTTTTTAGGGAAGATCTGGCCTTCCCACAAGGGAAGGCCAGGGAATTTTCTTCAGAGCAGACCAGAGCCAACAGCCCCACCAGAAGAGAGCTTCAGGTCTGGGGTAGAGACAACAACTCCCCCTCAGAAGCAGGAGCCGATAGACAAGGAACTGTATCCTTTAACTTCCCTCAGGTCACTCTTTGGCAACGACCCCTCGTCACAATAAAGATAGGGGGGCAACTAAAGGAAGCTCTATTAGATACAGGAGCAGATGATACAGTATTAGAAGAAATGAGTTTGCCAGGAAGATGGAAACCAAAAATGATAGGGGGAATTGGAGGTTTTATCAAAGTAAGACAGTATGATCAGATACTCATAGAAATCTGTGGACATAAAGCTATAGGTACAGTATTAGTAGGACCTACACCTGTCAACATAATTGGAAGAAATCTGTTGACTCAGATTGGTTGCACTTTAAATTTT",
    "SARS-CoV-2": "ATGTTTGTTTTTCTTGTTTTATTGCCACTAGTCTCTAGTCAGTGTGTTAATCTTACAACCAGAACTCAATTACCCCCTGCATACACTAATTCTTTCACACGTGGTGTTTATTACCCTGACAAAGTTTTCAGATCCTCAGTTTTACATTCAACTCAGGACTTGTTCTTACCTTTCTTTTCCAATGTTACTTGGTTCCATGCTATACATGTCTCTGGGACCAATGGTACTAAGAGGTTTGATAACCCTGTCCTACCATTTAATGATGGTGTTTATTTTGCTTCCACTGAGAAGTCTAACATAATAAGAGGCTGGATTTTTGGTACTACTTTAGATTCGAAGACCCAGTCCCTACTTATTGTTAATAACGCTACTAATGTTGTTATTAAAGTCTGTGAATTTCAATTTTGTAATGATCCATTTTTGGGTGTTTATTACCACAAAAACAACAAAAGTTGGATGGAAAGTGAGTTCAGAGTTTATTCTAGTGCGAATAATTGCACTTTTGAATATGTCTCTCAGCCTTTTCTTATGGACCTTGAAGGAAAACAGGGTAATTTCAAAAATCTTAGGGAATTTGTGTTTAAGAATATTGATGGTTATTTTAAAATATATTCTAAGCACACGCCTATTAATTTAGGGCGTGATCTCCCTCAGGGTTTTTCGGCTTTAGAACCATTGGTAGATTTGCCAATAGGTATTAACATCACTAGGTTTCAAACTTTACTTGCTTTACATAGAAGTTATTTGACTCCTGGTGATTCTTCTTCAGGTTGGACAGCTGGTGCTGCAGCTTATTATGTGGGTTATCTTCAACCTAGGACTTTTCTATTAAAATATAATGAAAATGGAACCATTACAGATGCTGTAGACTGTGCACTTGACCCTCTCTCAGAAACAAAGTGTACGTTGAAATCCTTCACTGTAGAAAAAGGAATCTATCAAACTTCTAACTTTAGAGTCCAACCAACAGAATCTATTGTTAGATTTCCTAATATTACAAACTTGTGCCCTTTTGGTGAAGTTTTTAACGCCACCAGATTTGCATCTGTTTATGCTTGGAACAGGAAGAGAATCAGCAACTGTGTTGCTGATTATTCTGTCCTATATAATTCCGCATCATTTTCCACTTTTAAGTGTTATGGAGTGTCTCCTACTAAATTAAATGATCTCTGCTTTACTAATGTCTATGCAGATTCATTTGTAATTAGAGGTGATGAAGTCAGACAAATCGCTCCAGGGCAAACTGGAAAGATTGCTGATTATAATTATAAATTACCAGATGATTTTACAGGCTGCGTTATAGCTTGGAATTCTAACAATCTTGATTCTAAGGTTGGTGGTAATTATAATTACCTGTATAGATTGTTTAGGAAGTCTAATCTCAAACCTTTTGAGAGAGATATTTCAACTGAAATCTATCAGGCCGGTAGCACACCTTGTAATGGTGTTGAAGGTTTTAATTGTTACTTTCCTTTACAATCATATGGTTTCCAACCCACTAATGGTGTTGGTTACCAACCATACAGAGTAGTAGTACTTTCTTTTGAACTTCTACATGCACCAGCAACTGTTTGTGGACCTAAAAAGTCTACTAATTTGGTTAAAAACAAATGTGTCAATTTCAACTTCAATGGTTTAACAGGCACAGGTGTTCTTACTGAGTCTAACAAAAAGTTTCTGCCTTTCCAACAATTTGGCAGAGACATTGCTGACACTACTGATGCTGTCCGTGATCCACAGACACTTGAGATTCTTGACATTACACCATGTTCTTTTGGTGGTGTCAGTGTTATAACACCAGGAACAAATACTTCTAACCAGGTTGCTGTTCTTTATCAGGATGTTAACTGCACAGAAGTCCCTGTTGCTATTCATGCAGATCAACTTACTCCTACTTGGCGTGTTTATTCTACAGG"
}

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Viral Evolution CRISPR Targeting API", "status": "active"}

@api_router.post("/sequence/upload", response_model=ViralSequence)
async def upload_sequence(sequence_data: SequenceUpload):
    """Upload a viral sequence for analysis"""
    try:
        # Validate sequence
        if not re.match(r'^[ATCGN]+$', sequence_data.sequence.upper()):
            raise HTTPException(status_code=400, detail="Invalid sequence format. Only ATCGN characters allowed.")
        
        sequence_obj = ViralSequence(
            name=sequence_data.name,
            sequence=sequence_data.sequence.upper(),
            virus_type=sequence_data.virus_type
        )
        
        # Store in database
        await db.viral_sequences.insert_one(sequence_obj.dict())
        return sequence_obj
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading sequence: {str(e)}")

@api_router.post("/sequence/analyze/{sequence_id}")
async def analyze_sequence(sequence_id: str):
    """Analyze a viral sequence for CRISPR targets"""
    try:
        # Get sequence from database
        sequence_doc = await db.viral_sequences.find_one({"id": sequence_id})
        if not sequence_doc:
            raise HTTPException(status_code=404, detail="Sequence not found")
        
        sequence = sequence_doc["sequence"]
        
        # Find CRISPR targets
        targets = crispr_analyzer.extract_target_sequences(sequence)
        
        # Analyze each target
        analyzed_targets = []
        for target in targets:
            conservation_score = crispr_analyzer.calculate_conservation_score(
                target["target_sequence"], 
                list(SAMPLE_SEQUENCES.values())
            )
            
            escape_prob = crispr_analyzer.predict_escape_probability(
                target["target_sequence"],
                target["gc_content"],
                conservation_score
            )
            
            binding_strength = crispr_analyzer.calculate_binding_strength(
                target["target_sequence"]
            )
            
            crispr_target = CRISPRTarget(
                sequence_id=sequence_id,
                target_sequence=target["target_sequence"],
                pam_sequence=target["pam_sequence"],
                position=target["position"],
                strand=target["strand"],
                gc_content=target["gc_content"],
                conservation_score=conservation_score,
                escape_probability=escape_prob,
                binding_strength=binding_strength
            )
            
            analyzed_targets.append(crispr_target)
            # Store target in database
            await db.crispr_targets.insert_one(crispr_target.dict())
        
        # Generate analysis summary
        high_confidence_targets = [t for t in analyzed_targets if t.escape_probability < 0.3 and t.binding_strength > 0.7]
        
        recommendations = []
        if high_confidence_targets:
            recommendations.append(f"Found {len(high_confidence_targets)} high-confidence targets with low escape probability")
            best_target = min(high_confidence_targets, key=lambda x: x.escape_probability)
            recommendations.append(f"Best target: {best_target.target_sequence} (escape prob: {best_target.escape_probability:.3f})")
        else:
            recommendations.append("No high-confidence targets found. Consider alternative approaches.")
        
        analysis_result = AnalysisResult(
            sequence_id=sequence_id,
            total_targets=len(analyzed_targets),
            high_confidence_targets=len(high_confidence_targets),
            conservation_data={
                "avg_conservation": np.mean([t.conservation_score for t in analyzed_targets]) if analyzed_targets else 0,
                "max_conservation": max([t.conservation_score for t in analyzed_targets]) if analyzed_targets else 0
            },
            escape_analysis={
                "avg_escape_prob": np.mean([t.escape_probability for t in analyzed_targets]) if analyzed_targets else 0,
                "min_escape_prob": min([t.escape_probability for t in analyzed_targets]) if analyzed_targets else 0
            },
            recommendations=recommendations
        )
        
        # Store analysis result
        await db.analysis_results.insert_one(analysis_result.dict())
        
        return {
            "analysis": analysis_result,
            "targets": analyzed_targets
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing sequence: {str(e)}")

@api_router.get("/sequence/{sequence_id}/targets")
async def get_targets(sequence_id: str):
    """Get CRISPR targets for a sequence"""
    targets = await db.crispr_targets.find({"sequence_id": sequence_id}).to_list(1000)
    return targets

@api_router.get("/samples")
async def get_sample_sequences():
    """Get sample viral sequences for testing"""
    return SAMPLE_SEQUENCES

@api_router.post("/samples/load/{virus_type}")
async def load_sample_sequence(virus_type: str):
    """Load a sample viral sequence"""
    if virus_type not in SAMPLE_SEQUENCES:
        raise HTTPException(status_code=404, detail="Sample sequence not found")
    
    sequence_data = SequenceUpload(
        name=f"Sample {virus_type}",
        sequence=SAMPLE_SEQUENCES[virus_type],
        virus_type=virus_type
    )
    
    return await upload_sequence(sequence_data)

@api_router.post("/simulate/mutation")
async def simulate_mutations(simulation: MutationSimulation):
    """Simulate viral mutations"""
    try:
        sequence = simulation.original_sequence
        mutations = []
        
        for gen in range(simulation.generations):
            if np.random.random() < simulation.mutation_rate:
                # Random mutation
                pos = np.random.randint(0, len(sequence))
                old_base = sequence[pos]
                new_base = np.random.choice(['A', 'T', 'C', 'G'])
                
                if old_base != new_base:
                    sequence = sequence[:pos] + new_base + sequence[pos+1:]
                    mutations.append({
                        "generation": gen,
                        "position": pos,
                        "from": old_base,
                        "to": new_base
                    })
        
        return {
            "original_sequence": simulation.original_sequence,
            "mutated_sequence": sequence,
            "mutations": mutations,
            "mutation_count": len(mutations)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error simulating mutations: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()