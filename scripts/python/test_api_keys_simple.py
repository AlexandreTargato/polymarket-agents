#!/usr/bin/env python3
"""
Simplified API Key Testing Script for Polymarket Agents

This script tests the core API connections without requiring OpenAI API key.
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.polymarket.polymarket import Polymarket
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON, AMOY


class SimpleAPIKeyTester:
    """Simplified API key testing for core functionality"""
    
    def __init__(self):
        self.results = {
            'perplexity_direct': {'status': 'not_tested', 'details': {}},
            'polygon_wallet': {'status': 'not_tested', 'details': {}},
            'polymarket_api': {'status': 'not_tested', 'details': {}},
            'timestamp': datetime.now().isoformat()
        }
    
    def test_perplexity_direct(self) -> Dict[str, Any]:
        """Test Perplexity API directly without structured parsing"""
        print("🔍 Testing Perplexity API directly...")
        
        try:
            # Check if API key is set
            api_key = os.getenv('PERPLEXITY_API_KEY')
            if not api_key:
                return {
                    'status': 'error',
                    'error': 'PERPLEXITY_API_KEY environment variable not set',
                    'details': {}
                }
            
            # Test direct API call
            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "sonar-deep-research",
                "messages": [
                    {
                        "role": "user",
                        "content": "What is the current price of Bitcoin? Please provide a brief analysis."
                    }
                ],
                "max_tokens": 100
            }
            
            print("   📡 Making direct API call...")
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                return {
                    'status': 'success',
                    'details': {
                        'api_key_present': True,
                        'api_key_length': len(api_key),
                        'api_call_successful': True,
                        'response_length': len(content),
                        'model_used': 'sonar-deep-research'
                    }
                }
            else:
                return {
                    'status': 'error',
                    'error': f'API call failed with status {response.status_code}: {response.text}',
                    'details': {
                        'api_key_present': True,
                        'api_key_length': len(api_key),
                        'api_call_successful': False,
                        'status_code': response.status_code
                    }
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'details': {
                    'api_key_present': bool(os.getenv('PERPLEXITY_API_KEY')),
                    'api_key_length': len(os.getenv('PERPLEXITY_API_KEY', ''))
                }
            }
    
    def test_polygon_wallet(self) -> Dict[str, Any]:
        """Test Polygon wallet connectivity"""
        print("💰 Testing Polygon wallet connectivity...")
        
        try:
            # Check if private key is set
            private_key = os.getenv('POLYGON_WALLET_PRIVATE_KEY')
            if not private_key:
                return {
                    'status': 'error',
                    'error': 'POLYGON_WALLET_PRIVATE_KEY environment variable not set',
                    'details': {}
                }
            
            # Test wallet key format (should be 64 hex characters)
            if not private_key.startswith('0x'):
                private_key = f'0x{private_key}'
            
            if len(private_key) != 66 or not all(c in '0123456789abcdefABCDEF' for c in private_key[2:]):
                return {
                    'status': 'error',
                    'error': 'Invalid private key format (should be 64 hex characters)',
                    'details': {
                        'key_length': len(private_key),
                        'key_format_valid': False
                    }
                }
            
            # Initialize Polymarket client
            polymarket = Polymarket()
            
            # Test wallet initialization
            if not polymarket.private_key:
                return {
                    'status': 'error',
                    'error': 'Failed to initialize wallet from private key',
                    'details': {
                        'key_present': True,
                        'key_length': len(private_key),
                        'wallet_initialized': False
                    }
                }
            
            # Test USDC balance retrieval
            print("   💳 Checking USDC balance...")
            try:
                balance = polymarket.get_usdc_balance()
                return {
                    'status': 'success',
                    'details': {
                        'key_present': True,
                        'key_length': len(private_key),
                        'key_format_valid': True,
                        'wallet_initialized': True,
                        'usdc_balance': balance,
                        'balance_retrieval_successful': True
                    }
                }
            except Exception as balance_error:
                return {
                    'status': 'warning',
                    'error': f'Wallet initialized but balance check failed: {str(balance_error)}',
                    'details': {
                        'key_present': True,
                        'key_length': len(private_key),
                        'key_format_valid': True,
                        'wallet_initialized': True,
                        'balance_retrieval_successful': False
                    }
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'details': {
                    'key_present': bool(os.getenv('POLYGON_WALLET_PRIVATE_KEY')),
                    'key_length': len(os.getenv('POLYGON_WALLET_PRIVATE_KEY', ''))
                }
            }
    
    def test_polymarket_api(self) -> Dict[str, Any]:
        """Test Polymarket API connectivity"""
        print("🏛️ Testing Polymarket API connectivity...")
        
        try:
            # Test CLOB client initialization
            host = "https://clob.polymarket.com"
            key = os.getenv("POLYGON_WALLET_PRIVATE_KEY")
            
            if not key:
                return {
                    'status': 'error',
                    'error': 'POLYGON_WALLET_PRIVATE_KEY required for Polymarket API test',
                    'details': {}
                }
            
            # Initialize CLOB client
            client = ClobClient(host, key=key, chain_id=POLYGON)
            
            # Test API credentials creation
            print("   🔑 Creating API credentials...")
            creds = client.create_or_derive_api_creds()
            
            if not creds:
                return {
                    'status': 'error',
                    'error': 'Failed to create API credentials',
                    'details': {
                        'clob_client_initialized': True,
                        'api_creds_created': False
                    }
                }
            
            # Test market data retrieval
            print("   📊 Testing market data retrieval...")
            try:
                markets = client.get_simplified_markets()
                return {
                    'status': 'success',
                    'details': {
                        'clob_client_initialized': True,
                        'api_creds_created': True,
                        'market_data_retrieval_successful': True,
                        'markets_count': len(markets) if markets else 0
                    }
                }
            except Exception as market_error:
                return {
                    'status': 'warning',
                    'error': f'API credentials created but market data retrieval failed: {str(market_error)}',
                    'details': {
                        'clob_client_initialized': True,
                        'api_creds_created': True,
                        'market_data_retrieval_successful': False
                    }
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'details': {
                    'clob_client_initialized': False
                }
            }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all API tests"""
        print("🚀 Starting Simplified API Key Tests for Polymarket Agents")
        print("=" * 60)
        
        # Test Perplexity API directly
        self.results['perplexity_direct'] = self.test_perplexity_direct()
        
        # Test Polygon wallet
        self.results['polygon_wallet'] = self.test_polygon_wallet()
        
        # Test Polymarket API
        self.results['polymarket_api'] = self.test_polymarket_api()
        
        # Print summary
        self.print_summary()
        
        return self.results
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📋 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        for api_name, result in self.results.items():
            if api_name == 'timestamp':
                continue
                
            status_emoji = {
                'success': '✅',
                'warning': '⚠️',
                'error': '❌',
                'not_tested': '⏸️'
            }.get(result['status'], '❓')
            
            print(f"{status_emoji} {api_name.upper().replace('_', ' ')}: {result['status'].upper()}")
            
            if result['status'] == 'error' and 'error' in result:
                print(f"   Error: {result['error']}")
            elif result['status'] == 'warning' and 'error' in result:
                print(f"   Warning: {result['error']}")
            
            if 'details' in result and result['details']:
                for key, value in result['details'].items():
                    print(f"   {key}: {value}")
            print()
        
        # Overall status
        all_success = all(
            result['status'] in ['success', 'warning'] 
            for name, result in self.results.items() 
            if name != 'timestamp'
        )
        
        if all_success:
            print("🎉 All core API keys are working! You're ready to start trading.")
            print("💡 Note: For full research functionality, you may want to add OPENAI_API_KEY to your .env file")
        else:
            print("⚠️ Some API keys need attention. Please check the errors above.")
    
    def save_results(self, filename: str = "simple_api_test_results.json"):
        """Save test results to file"""
        results_path = Path(__file__).parent / filename
        with open(results_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"📄 Results saved to: {results_path}")


def main():
    """Main function to run API key tests"""
    print("Polymarket Agents - Simplified API Key Testing")
    print("==============================================")
    
    # Check if .env file exists
    env_path = Path(__file__).parent.parent.parent / '.env'
    if not env_path.exists():
        print("⚠️ Warning: .env file not found. Make sure to set your environment variables.")
        print("   Required variables:")
        print("   - PERPLEXITY_API_KEY")
        print("   - POLYGON_WALLET_PRIVATE_KEY")
        print("   - OPENAI_API_KEY (optional, for full research functionality)")
        print()
    
    # Run tests
    tester = SimpleAPIKeyTester()
    results = tester.run_all_tests()
    
    # Save results
    tester.save_results()
    
    # Exit with appropriate code
    all_success = all(
        result['status'] in ['success', 'warning'] 
        for name, result in results.items() 
        if name != 'timestamp'
    )
    
    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
