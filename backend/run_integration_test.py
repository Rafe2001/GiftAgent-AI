import urllib.request
import json
import time
import sys

# Aarav Mehta sample data
contact_data = {
  "contacts": [
    {
      "name": "Aarav Mehta",
      "role": "VP Sales",
      "company": "Acme Corp",
      "location": "Bengaluru, India",
      "linkedin_profile": {
        "headline": "VP Sales at Acme Corp | Enterprise SaaS | GTM Leadership",
        "about": "I enjoy building high-performing revenue teams and scaling SaaS businesses across India and Southeast Asia.",
        "experience": [
          {
            "title": "VP Sales",
            "company": "Acme Corp",
            "description": "Leading enterprise sales, strategic accounts, and GTM expansion."
          }
        ],
        "recent_posts": [
          "Great sales teams are built on trust, coaching, and consistency.",
          "Still recovering from yesterday's India vs Australia match. What a game!"
        ],
        "recent_comments": [
          "Cricket teaches leadership better than most management books."
        ],
        "engaged_topics": ["Cricket", "Revenue leadership", "SaaS GTM", "Team building"]
      },
      "relationship_context": {
        "relationship_type": "Prospective customer",
        "last_interaction": "Positive discovery call last week",
        "business_goal": "Nurture relationship before follow-up meeting"
      },
      "gift_context": {
        "occasion": "Post-meeting thank you",
        "budget_min": 3000,
        "budget_max": 5000,
        "currency": "INR",
        "country": "India"
      }
    }
  ]
}

def run_test():
    # 1. Upload contact
    print("1. Uploading contact to API...")
    req = urllib.request.Request(
        "http://localhost:8000/api/contacts/upload",
        data=json.dumps(contact_data).encode(),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req) as res:
            upload_res = json.loads(res.read().decode())
            contact_id = upload_res["contacts"][0]["contact_id"]
            print(f"✅ Uploaded successfully! Contact ID: {contact_id}")
    except Exception as e:
        print("❌ Upload failed. Make sure the FastAPI server is running on port 8000.", e)
        sys.exit(1)

    # 2. Trigger recommendation generation
    print("\n2. Triggering recommendation workflow...")
    req_gen = urllib.request.Request(
        "http://localhost:8000/api/recommendations/generate",
        data=b"",
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req_gen) as res:
            print("✅ Recommendation workflow triggered successfully.")
    except Exception as e:
        print("❌ Trigger failed:", e)
        sys.exit(1)

    # 3. Poll status
    print("\n3. Polling recommendation status (checking graph nodes execution)...")
    get_url = f"http://localhost:8000/api/recommendations/{contact_id}"
    
    # Poll for up to 90 seconds (each iteration 5 seconds)
    for i in range(18):
        time.sleep(5)
        try:
            with urllib.request.urlopen(get_url) as res:
                data = json.loads(res.read().decode())
                status = data.get("workflow_status")
                step = data.get("current_step")
                print(f"Poll #{i+1}: status={status}, current_step={step}")
                
                if status in ("completed", "completed_with_issues"):
                    print("\n🎉 Recommendation generation finalized!")
                    print(f"Number of gifts recommended: {len(data.get('recommended_gifts', []))}")
                    print("\nRecommended Gifts:")
                    for gift in data.get("recommended_gifts", []):
                        print(f"- Rank {gift.get('rank')}: {gift.get('gift_name')} from {gift.get('store')} ({gift.get('estimated_price')})")
                        print(f"  Confidence: {gift.get('confidence_score')}")
                        print(f"  URL: {gift.get('product_url')}")
                        print(f"  Reason: {gift.get('why_this_gift')}")
                        print(f"  Message: {gift.get('personalised_message')}")
                    break
                elif status == "failed":
                    print("❌ Workflow execution failed!")
                    print(json.dumps(data, indent=2))
                    sys.exit(1)
        except Exception as e:
            print("Poll error:", e)
    else:
        print("❌ Timeout waiting for recommendation generation.")
        sys.exit(1)

if __name__ == "__main__":
    run_test()
