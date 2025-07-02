import requests
import json
import time
import sys

class ViralCRISPRTester:
    def __init__(self, base_url="https://7d3f17f7-1d09-40ff-935f-d9f9976a2f45.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.sequence_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"Response: {response.text}")
                except:
                    pass
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_api_root(self):
        """Test the API root endpoint"""
        success, response = self.run_test(
            "API Root",
            "GET",
            "",
            200
        )
        if success:
            print(f"API Message: {response.get('message', 'No message')}")
        return success

    def test_get_samples(self):
        """Test getting sample sequences"""
        success, response = self.run_test(
            "Get Sample Sequences",
            "GET",
            "samples",
            200
        )
        if success:
            print(f"Found {len(response)} sample sequences")
            for virus_type in response:
                print(f"  - {virus_type}: {len(response[virus_type])} bp")
        return success

    def test_load_sample(self, virus_type="HIV-1"):
        """Test loading a sample sequence"""
        success, response = self.run_test(
            f"Load Sample Sequence ({virus_type})",
            "POST",
            f"samples/load/{virus_type}",
            200
        )
        if success:
            self.sequence_id = response.get('id')
            print(f"Loaded sequence ID: {self.sequence_id}")
            print(f"Sequence name: {response.get('name')}")
            print(f"Sequence length: {len(response.get('sequence', ''))}")
        return success

    def test_sequence_analysis(self):
        """Test sequence analysis"""
        if not self.sequence_id:
            print("❌ No sequence ID available for analysis")
            return False
            
        success, response = self.run_test(
            "Analyze Sequence",
            "POST",
            f"sequence/analyze/{self.sequence_id}",
            200
        )
        if success:
            analysis = response.get('analysis', {})
            targets = response.get('targets', [])
            print(f"Analysis results:")
            print(f"  - Total targets: {analysis.get('total_targets', 0)}")
            print(f"  - High confidence targets: {analysis.get('high_confidence_targets', 0)}")
            print(f"  - Number of targets returned: {len(targets)}")
            
            if targets:
                print("\nSample target details:")
                target = targets[0]
                print(f"  - Target sequence: {target.get('target_sequence')}")
                print(f"  - Position: {target.get('position')}")
                print(f"  - Conservation score: {target.get('conservation_score')}")
                print(f"  - Escape probability: {target.get('escape_probability')}")
        return success

    def test_mutation_simulation(self):
        """Test mutation simulation"""
        test_data = {
            "original_sequence": "ATGGGTGCGAGAGCGTCAGTATTAAGCGGGGGAGAATTAGATCGATGGGAAAAAATTCGGTTAAGGCCAGGGGGAAAGAAAAAATATAAATTAAAACATATAGTATGGGCAAGCAGGGAGCTAGAACGATTCGCAGTTAATCCTGGCCTGTTAGAAACATCAGAAGGCTGTAGACAAATACTGGGACAGCTACAACCATCCCTTCAGACAGGATCAGAAGAACTTAGATCATTATATAATACAGTAGCAACCCTCTATTGTGTGCATCAAAGGATAGAGATAAAAGACACCAAGGAAGCTTTAGACAAGATAGAGGAAGAGCAAAACAAAAGTAAGAAAAAAGCACAGCAAGCAGCAGCTGACACAGGACACAGCAATCAGGTCAGCCAAAATTACCCTATAGTGCAGAACATCCAGGGGCAAATGGTACATCAGGCCATATCACCTAGAACTTTAAATGCATGGGTAAAAGTAGTAGAAGAGAAGGCTTTCAGCCCAGAAGTGATACCCATGTTTTCAGCATTATCAGAAGGAGCCACCCCACAAGATTTAAACACCATGCTAAACACAGTGGGGGGACATCAAGCAGCCATGCAAATGTTAAAAGAGACCATCAATGAGGAAGCTGCAGAATGGGATAGAGTGCATCCAGTGCATGCAGGGCCTATTGCACCAGGCCAGATGAGAGAACCAAGGGGAAGTGACATAGCAGGAACTACTAGTACCCTTCAGGAACAAATAGGATGGATGACAAATAATCCACCTATCCCAGTAGGAGAAATTTATAAAAGATGGATAATCCTGGGATTAAATAAAATAGTAAGAATGTATAGCCCTACCAGCATTCTGGACATAAGACAAGGACCAAAGGAACCCTTTAGAGACTATGTAGACCGGTTCTATAAAACTCTAAGAGCCGAGCAAGCTTCACAGGAGGTAAAAAATTGGATGACAGAAACCTTGTTGGTCCAAAATGCGAACCCAGATTGTAAGACTATTTTAAAAGCATTGGGACCAGGGGCTACACTAGAAGAAATGATGACAGCATGTCAGGGAGTAGGAGGACCCGGCCATAAAGCAAGAGTTTTGGCTGAAGCAATGAGCCAAGTAACAAATTCAGCTACCATAATGATGCAGAGAGGCAATTTTAGGAACCAAAGAAAGATTGTTAAGTGTTTCAATTGTGGCAAAGAAGGGCACACAGCCAGAAATTGCAGGGCCCCTAGGAAAAAGGGCTGTTGGAAATGTGGAAAGGAAGGACACCAAATGAAAGATTGTACTGAGAGACAGGCTAATTTTTTAGGGAAGATCTGGCCTTCCCACAAGGGAAGGCCAGGGAATTTTCTTCAGAGCAGACCAGAGCCAACAGCCCCACCAGAAGAGAGCTTCAGGTCTGGGGTAGAGACAACAACTCCCCCTCAGAAGCAGGAGCCGATAGACAAGGAACTGTATCCTTTAACTTCCCTCAGGTCACTCTTTGGCAACGACCCCTCGTCACAATAAAGATAGGGGGGCAACTAAAGGAAGCTCTATTAGATACAGGAGCAGATGATACAGTATTAGAAGAAATGAGTTTGCCAGGAAGATGGAAACCAAAAATGATAGGGGGAATTGGAGGTTTTATCAAAGTAAGACAGTATGATCAGATACTCATAGAAATCTGTGGACATAAAGCTATAGGTACAGTATTAGTAGGACCTACACCTGTCAACATAATTGGAAGAAATCTGTTGACTCAGATTGGTTGCACTTTAAATTTT",
            "mutation_rate": 0.01,
            "generations": 100
        }
        
        success, response = self.run_test(
            "Simulate Mutations",
            "POST",
            "simulate/mutation",
            200,
            data=test_data
        )
        if success:
            print(f"Mutation simulation results:")
            print(f"  - Mutations generated: {response.get('mutation_count', 0)}")
            if response.get('mutations'):
                print(f"  - Sample mutations:")
                for mutation in response.get('mutations')[:3]:
                    print(f"    - Gen {mutation.get('generation')}: {mutation.get('from')} → {mutation.get('to')} at position {mutation.get('position')}")
        return success

def main():
    # Setup
    tester = ViralCRISPRTester()
    
    # Run tests
    print("\n===== Testing Viral Evolution CRISPR Targeting API =====\n")
    
    # Test 1: API Root
    tester.test_api_root()
    
    # Test 2: Get Samples
    tester.test_get_samples()
    
    # Test 3: Load Sample
    tester.test_load_sample("HIV-1")
    
    # Test 4: Sequence Analysis
    tester.test_sequence_analysis()
    
    # Test 5: Mutation Simulation
    tester.test_mutation_simulation()
    
    # Print results
    print(f"\n===== Test Results =====")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())