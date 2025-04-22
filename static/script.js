// Function to scroll to the bottom of the workflow container
function scrollToBottom() {
    const workflowContainer = document.getElementById('workflow-container');
    if (workflowContainer) {
        workflowContainer.scrollTop = workflowContainer.scrollHeight;
    }
}

// Auto-scroll when new steps are added
const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
            scrollToBottom();
        }
    });
});

document.addEventListener('DOMContentLoaded', () => {
    const workflowContainer = document.getElementById('workflow-container');
    if (workflowContainer) {
        observer.observe(workflowContainer, { childList: true, subtree: true });
    }
    
    // Initial setup code here
    const runButton = document.getElementById('run-button');
    const jiraUrlInput = document.getElementById('jira-url');
    
    runButton.addEventListener('click', async () => {
        const jiraUrl = jiraUrlInput.value.trim();
        if (!jiraUrl) {
            alert('Please enter a JIRA URL');
            return;
        }
        
        // Clear previous results
        const workflowContainer = document.getElementById('workflow-container');
        workflowContainer.innerHTML = '';
        
        // Disable the run button while processing
        runButton.disabled = true;
        runButton.textContent = 'Processing...';
        
        try {
            const response = await fetch('/run', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ jira_url: jiraUrl }),
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            // Process the response
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const text = decoder.decode(value, { stream: true });
                const lines = text.split('\n').filter(line => line.trim());
                
                for (const line of lines) {
                    try {
                        if (line.trim()) {
                            const data = JSON.parse(line);
                            addStep(data);
                        }
                    } catch (e) {
                        console.error('Error parsing JSON:', e, line);
                    }
                }
            }
        } catch (error) {
            console.error('Error:', error);
            addStep({
                type: 'error',
                title: 'Error',
                content: error.message,
            });
        } finally {
            // Re-enable the run button
            runButton.disabled = false;
            runButton.textContent = 'Run Workflow';
            scrollToBottom();
        }
    });
});

function addStep(step) {
    const workflowContainer = document.getElementById('workflow-container');
    const stepElement = document.createElement('div');
    stepElement.className = 'step';
    stepElement.setAttribute('data-type', step.type);
    if (step.title) {
        stepElement.setAttribute('data-title', step.title);
    }
    
    const titleElement = document.createElement('div');
    titleElement.className = 'step-title';
    titleElement.textContent = step.title || '';
    
    const contentElement = document.createElement('div');
    contentElement.className = 'step-content';
    contentElement.textContent = step.content || '';
    
    stepElement.appendChild(titleElement);
    stepElement.appendChild(contentElement);
    workflowContainer.appendChild(stepElement);
    
    scrollToBottom();
} 