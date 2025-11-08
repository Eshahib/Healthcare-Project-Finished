"""
Test script to verify NeuralSeek API connection
"""
import os
from dotenv import load_dotenv
from neuralseek import analyze_symptoms_with_neuralseek

load_dotenv()

def test_neuralseek():
    """Test NeuralSeek API connection"""
    print("🧪 Testing NeuralSeek API Connection...")
    print(f"API URL: {os.getenv('NEURALSEEK_API_URL')}")
    print(f"API Key: {os.getenv('NEURALSEEK_API_KEY')[:20]}...")
    print()
    
    try:
        # Test with sample symptoms
        test_symptoms = ["Fever", "Cough", "Headache"]
        test_comments = "Started 2 days ago, getting worse"
        
        print(f"📋 Testing with symptoms: {test_symptoms}")
        print(f"💬 Comments: {test_comments}")
        print()
        
        result = analyze_symptoms_with_neuralseek(
            symptoms=test_symptoms,
            comments=test_comments
        )
        
        print("✅ NeuralSeek API connection successful!")
        print()
        print("📊 Analysis Result:")
        print(f"   Diagnosis: {result['diagnosis_text'][:200]}...")
        print(f"   Confidence: {result['confidence_score']}")
        print(f"   Possible Conditions: {result['possible_conditions']}")
        print(f"   Recommendations: {result['recommendations'][:200] if result['recommendations'] else 'N/A'}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print()
        print("💡 Troubleshooting:")
        print("   1. Check that your API key is correct")
        print("   2. Verify the API URL is correct")
        print("   3. Check your NeuralSeek account has API access enabled")
        print("   4. Verify your network connection")
        return False

if __name__ == "__main__":
    test_neuralseek()

