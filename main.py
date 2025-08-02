import os
from fastapi.staticfiles import StaticFiles
import uvicorn

# Import your application
from app import app

# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)

# Create a simple HTML file if it doesn't exist
if not os.path.exists("static/index.html"):
    with open("static/index.html", "w") as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM Document Processing System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            padding: 20px;
        }
        .container {
            max-width: 1000px;
        }
        .result-card {
            margin-top: 20px;
            display: none;
        }
        .clause-card {
            margin-top: 10px;
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
        }
        .loader {
            display: none;
            border: 5px solid #f3f3f3;
            border-top: 5px solid #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 2s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="mb-4">LLM Document Processing System</h1>
        
        <div class="card mb-4">
            <div class="card-header">Upload Documents</div>
            <div class="card-body">
                <form id="upload-form">
                    <div class="mb-3">
                        <label for="document" class="form-label">Document File (PDF, DOCX, TXT, EML)</label>
                        <input type="file" class="form-control" id="document" required>
                    </div>
                    <div class="mb-3">
                        <label for="metadata" class="form-label">Metadata (JSON)</label>
                        <textarea class="form-control" id="metadata" rows="3" placeholder='{"type": "insurance_policy", "effective_date": "2023-01-01"}'></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary">Upload</button>
                </form>
                <div id="upload-status" class="mt-3"></div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">Process Query</div>
            <div class="card-body">
                <form id="query-form">
                    <div class="mb-3">
                        <label for="query" class="form-label">Query</label>
                        <input type="text" class="form-control" id="query" placeholder="46-year-old male, knee surgery in Pune, 3-month-old insurance policy" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Process</button>
                </form>
                <div id="loader" class="loader"></div>
            </div>
        </div>
        
        <div id="result-card" class="card result-card">
            <div class="card-header">Result</div>
            <div class="card-body">
                <div class="row mb-3">
                    <div class="col-md-6">
                        <h5>Decision</h5>
                        <p id="decision"></p>
                    </div>
                    <div class="col-md-6">
                        <h5>Amount</h5>
                        <p id="amount"></p>
                    </div>
                </div>
                <div class="mb-3">
                    <h5>Justification</h5>
                    <p id="justification"></p>
                </div>
                <div class="mb-3">
                    <h5>Clause References</h5>
                    <p id="clause-refs"></p>
                </div>
                <div class="mb-3">
                    <h5>Structured Query</h5>
                    <pre id="structured-query" class="bg-light p-2 rounded"></pre>
                </div>
                <div class="mb-3">
                    <h5>Relevant Clauses</h5>
                    <div id="relevant-clauses"></div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        document.getElementById('upload-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('document');
            const metadataInput = document.getElementById('metadata');
            const statusDiv = document.getElementById('upload-status');
            
            if (!fileInput.files[0]) {
                statusDiv.innerHTML = '<div class="alert alert-danger">Please select a file</div>';
                return;
            }
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            
            let metadata = "{}";
            try {
                // Validate JSON
                if (metadataInput.value.trim()) {
                    JSON.parse(metadataInput.value);
                    metadata = metadataInput.value;
                }
            } catch (error) {
                statusDiv.innerHTML = '<div class="alert alert-danger">Invalid JSON metadata</div>';
                return;
            }
            
            formData.append('metadata', metadata);
            
            statusDiv.innerHTML = '<div class="alert alert-info">Uploading...</div>';
            
            try {
                const response = await fetch('/upload_document', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    statusDiv.innerHTML = `<div class="alert alert-success">${result.message}</div>`;
                } else {
                    statusDiv.innerHTML = `<div class="alert alert-danger">${result.detail || 'Upload failed'}</div>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
            }
        });
        
        document.getElementById('query-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const queryInput = document.getElementById('query');
            const loader = document.getElementById('loader');
            const resultCard = document.getElementById('result-card');
            
            if (!queryInput.value.trim()) {
                return;
            }
            
            // Show loader, hide result
            loader.style.display = 'block';
            resultCard.style.display = 'none';
            
            try {
                const response = await fetch('/process_query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        query: queryInput.value
                    })
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    // Update result card
                    document.getElementById('decision').textContent = result.decision.toUpperCase();
                    document.getElementById('amount').textContent = result.amount ? `$${result.amount}` : 'N/A';
                    document.getElementById('justification').textContent = result.justification;
                    document.getElementById('clause-refs').textContent = result.clause_references.join(', ');
                    document.getElementById('structured-query').textContent = JSON.stringify(result.structured_query, null, 2);
                    
                    // Render relevant clauses
                    const clausesDiv = document.getElementById('relevant-clauses');
                    clausesDiv.innerHTML = '';
                    
                    result.relevant_clauses.forEach((clause, index) => {
                        const clauseCard = document.createElement('div');
                        clauseCard.className = 'clause-card';
                        clauseCard.innerHTML = `
                            <h6>Clause ${index + 1} (Score: ${Math.round(clause.score * 100)}%)</h6>
                            <p>${clause.content}</p>
                        `;
                        clausesDiv.appendChild(clauseCard);
                    });
                    
                    // Show result
                    resultCard.style.display = 'block';
                } else {
                    alert(`Error: ${result.detail || 'Processing failed'}`);
                }
            } catch (error) {
                alert(`Error: ${error.message}`);
            } finally {
                loader.style.display = 'none';
            }
        });
    </script>
</body>
</html>""")

# Mount static files
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    print("Starting LLM Document Processing System...")
    print("Using local models for query parsing and decision making")
    print("The system is starting up - this might take a minute for the first run as models are downloaded")
    
    # Run the application
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)