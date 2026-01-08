"""
Test script for Exercise 2: Test partner's API
Makes 10 predictions and compares results with local model
"""
import requests
import json
import sys
from typing import List, Dict
import joblib
import pandas as pd
import numpy as np


def generate_test_customers(n: int = 10) -> List[Dict]:
    """Generate test customer data for predictions"""
    np.random.seed(42)
    
    customers = []
    for i in range(n):
        # Generate realistic customer data
        geography = np.random.choice(['France', 'Germany', 'Spain'])
        customer = {
            "CreditScore": int(np.random.randint(400, 850)),
            "Age": int(np.random.randint(25, 70)),
            "Tenure": int(np.random.randint(0, 11)),
            "Balance": float(np.random.uniform(0, 200000)),
            "NumOfProducts": int(np.random.randint(1, 5)),
            "HasCrCard": int(np.random.choice([0, 1])),
            "IsActiveMember": int(np.random.choice([0, 1])),
            "EstimatedSalary": float(np.random.uniform(20000, 150000)),
            "Geography_Germany": 1 if geography == 'Germany' else 0,
            "Geography_Spain": 1 if geography == 'Spain' else 0
        }
        customers.append(customer)
    
    return customers


def test_partner_api(api_url: str) -> List[Dict]:
    """Test partner's API with 10 predictions"""
    customers = generate_test_customers(10)
    results = []
    
    print(f"🌐 Testing partner API: {api_url}")
    print("=" * 60)
    
    # Test health check first
    try:
        health_response = requests.get(f"{api_url}/health", timeout=10)
        print(f"✓ Health check: {health_response.status_code}")
        if health_response.status_code == 200:
            print(f"  {health_response.json()}")
    except Exception as e:
        print(f"⚠ Health check failed: {e}")
    
    print("\n" + "=" * 60)
    print("Making 10 predictions...")
    print("=" * 60 + "\n")
    
    # Make 10 predictions
    for i, customer in enumerate(customers, 1):
        try:
            response = requests.post(
                f"{api_url}/predict",
                json=customer,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                results.append({
                    "customer_id": i,
                    "customer_data": customer,
                    "prediction": result
                })
                print(f"✓ Prediction {i}/10:")
                print(f"  Churn Probability: {result['churn_probability']:.4f}")
                print(f"  Prediction: {'CHURN' if result['prediction'] == 1 else 'NO CHURN'}")
                print(f"  Risk Level: {result['risk_level']}")
            else:
                print(f"✗ Prediction {i}/10 failed: {response.status_code}")
                print(f"  Response: {response.text}")
        
        except requests.exceptions.Timeout:
            print(f"✗ Prediction {i}/10 timeout (>10s)")
        except Exception as e:
            print(f"✗ Prediction {i}/10 error: {e}")
    
    return results


def compare_with_local_model(results: List[Dict], model_path: str = "model/churn_model.pkl"):
    """Compare partner API results with local model predictions"""
    try:
        # Load local model
        model = joblib.load(model_path)
        print("\n" + "=" * 60)
        print("📊 Comparing with local model...")
        print("=" * 60 + "\n")
        
        differences = []
        
        for result in results:
            customer_data = result["customer_data"]
            partner_pred = result["prediction"]
            
            # Prepare data for local model (same order as training)
            features = pd.DataFrame([{
                'CreditScore': customer_data['CreditScore'],
                'Age': customer_data['Age'],
                'Tenure': customer_data['Tenure'],
                'Balance': customer_data['Balance'],
                'NumOfProducts': customer_data['NumOfProducts'],
                'HasCrCard': customer_data['HasCrCard'],
                'IsActiveMember': customer_data['IsActiveMember'],
                'EstimatedSalary': customer_data['EstimatedSalary'],
                'Geography_Germany': customer_data['Geography_Germany'],
                'Geography_Spain': customer_data['Geography_Spain']
            }])
            
            # Local prediction
            local_prob = model.predict_proba(features)[0][1]
            local_class = model.predict(features)[0]
            
            # Calculate difference
            prob_diff = abs(partner_pred['churn_probability'] - local_prob)
            class_match = partner_pred['prediction'] == local_class
            
            differences.append({
                'customer_id': result['customer_id'],
                'partner_prob': partner_pred['churn_probability'],
                'local_prob': local_prob,
                'prob_diff': prob_diff,
                'partner_class': partner_pred['prediction'],
                'local_class': local_class,
                'class_match': class_match
            })
            
            match_symbol = "✓" if class_match else "✗"
            print(f"{match_symbol} Customer {result['customer_id']}:")
            print(f"  Partner: {partner_pred['churn_probability']:.4f} → {partner_pred['prediction']}")
            print(f"  Local:   {local_prob:.4f} → {local_class}")
            print(f"  Diff:    {prob_diff:.4f}\n")
        
        # Summary statistics
        print("=" * 60)
        print("📈 Summary Statistics")
        print("=" * 60)
        avg_diff = np.mean([d['prob_diff'] for d in differences])
        max_diff = np.max([d['prob_diff'] for d in differences])
        agreement = sum([d['class_match'] for d in differences]) / len(differences) * 100
        
        print(f"Average probability difference: {avg_diff:.4f}")
        print(f"Maximum probability difference: {max_diff:.4f}")
        print(f"Classification agreement: {agreement:.1f}%")
        
        return differences
    
    except FileNotFoundError:
        print(f"⚠ Local model not found at {model_path}")
        print("  Skipping comparison...")
        return []
    except Exception as e:
        print(f"⚠ Error comparing with local model: {e}")
        return []


def save_results(results: List[Dict], differences: List[Dict], filename: str = "resultat.txt"):
    """Save results to resultat.txt"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("EXERCISE 2 - PARTNER API TEST RESULTS\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Total predictions: {len(results)}\n\n")
        
        for result in results:
            f.write(f"Customer {result['customer_id']}:\n")
            f.write(f"  Input: {json.dumps(result['customer_data'], indent=4)}\n")
            f.write(f"  Prediction: {json.dumps(result['prediction'], indent=4)}\n")
            f.write("\n")
        
        if differences:
            f.write("\n" + "=" * 80 + "\n")
            f.write("COMPARISON WITH LOCAL MODEL\n")
            f.write("=" * 80 + "\n\n")
            
            for diff in differences:
                match = "✓ MATCH" if diff['class_match'] else "✗ MISMATCH"
                f.write(f"Customer {diff['customer_id']}: {match}\n")
                f.write(f"  Partner probability: {diff['partner_prob']:.4f} → Class {diff['partner_class']}\n")
                f.write(f"  Local probability:   {diff['local_prob']:.4f} → Class {diff['local_class']}\n")
                f.write(f"  Difference:          {diff['prob_diff']:.4f}\n\n")
            
            avg_diff = np.mean([d['prob_diff'] for d in differences])
            max_diff = np.max([d['prob_diff'] for d in differences])
            agreement = sum([d['class_match'] for d in differences]) / len(differences) * 100
            
            f.write("\nSummary:\n")
            f.write(f"  Average difference: {avg_diff:.4f}\n")
            f.write(f"  Maximum difference: {max_diff:.4f}\n")
            f.write(f"  Agreement rate:     {agreement:.1f}%\n")
    
    print(f"\n✓ Results saved to {filename}")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python tests/test_partner_api.py <PARTNER_API_URL>")
        print("\nExample:")
        print("  python tests/test_partner_api.py https://partner-api.azurecontainerapps.io")
        sys.exit(1)
    
    api_url = sys.argv[1].rstrip('/')
    
    # Test partner API
    results = test_partner_api(api_url)
    
    if not results:
        print("\n⚠ No successful predictions. Cannot continue.")
        sys.exit(1)
    
    # Compare with local model
    differences = compare_with_local_model(results)
    
    # Save results
    save_results(results, differences)
    
    print("\n" + "=" * 60)
    print("✓ Exercise 2 completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
