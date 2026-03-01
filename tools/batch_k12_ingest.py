import os
import subprocess

# Define the full spectrum of K-12 knowledge we want The Kid to ingest.
# These will be queried via Wikipedia using our curriculum_downloader.py

CURRICULUM = {
    "Science": [
        "Solar System", "Water Cycle", "Photosynthesis", 
        "Human body", "Periodic Table", "Newton's laws of motion",
        "Theory of relativity", "Quantum mechanics", "Genetics", "Evolution",
        "Climate change", "Ecology", "Cell biology"
    ],
    "History": [
        "Ancient Egypt", "Roman Empire", "Middle Ages", "Renaissance",
        "Industrial Revolution", "American Revolutionary War", "World War I", 
        "World War II", "Cold War", "Civil rights movement", "Space Race"
    ],
    "Geography": [
        "Continents", "Oceans", "Amazon Rainforest", "Mount Everest",
        "Sahara Desert", "Plate tectonics", "Meteorology", "Cartography"
    ],
    "Life_Skills": [
        "Nutrition", "Personal finance", "First aid", "Agriculture", 
        "Computer science", "Internet", "Artificial intelligence"
    ]
}

def main():
    print("====================================================")
    print("   THE KID - K-12 BATCH CURRICULUM INGESTION        ")
    print("====================================================")
    
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    downloader_script = os.path.join(tools_dir, "curriculum_downloader.py")
    
    total_topics = sum(len(topics) for topics in CURRICULUM.values())
    print(f"Beginning batch download of {total_topics} macro-topics...\n")

    for category, topics in CURRICULUM.items():
        print(f"\n--- Ingesting {category.upper()} ---")
        # We process in batches of 5 to avoid overloading terminal output
        chunks = [topics[i:i + 5] for i in range(0, len(topics), 5)]
        
        for chunk in chunks:
            batch_string = ",".join(chunk)
            cmd = ["uv", "run", "python", downloader_script, "--batch", batch_string, "--category", category]
            
            try:
                # Run the downloader synchronously
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error downloading batch: {batch_string}. Error: {e}")

    print("\n====================================================")
    print("   K-12 INGESTION COMPLETE. BACKGROUND LEARNER QUEUED. ")
    print("====================================================")

if __name__ == "__main__":
    main()
