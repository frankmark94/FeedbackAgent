// DOM Elements
const form = document.getElementById('feedback-form');
const jqlInput = document.getElementById('jql');
const maxResultsInput = document.getElementById('max-results');
const persistThreadCheckbox = document.getElementById('persist-thread');
const postToJiraCheckbox = document.getElementById('post-to-jira');
const createMockFeedbackCheckbox = document.getElementById('create-mock-feedback');
const mockFeedbackContainer = document.getElementById('mock-feedback-container');
const mockItemsList = document.getElementById('mock-items-list');
const addMockItemBtn = document.getElementById('add-mock-item-btn');
const analyzeBtn = document.getElementById('analyze-btn');
const aiMockButton = document.getElementById('ai-mock-button');
const workflowCard = document.getElementById('workflow-card');
const workflowSteps = document.getElementById('workflow-steps');
const workflowStatus = document.getElementById('workflow-status');
const workflowStatusText = document.getElementById('workflow-status-text');
const resultsCard = document.getElementById('results-card');
const resultsContainer = document.getElementById('results-container');
const loadingOverlay = document.getElementById('loading-overlay');
const loadingText = document.getElementById('loading-text');

// Templates
const workflowStepTemplate = document.getElementById('workflow-step-template');
const resultTemplate = document.getElementById('result-template');
const mockFeedbackItemTemplate = document.getElementById('mock-feedback-item-template');

// Global state
let currentWorkflowId = null;
let mockItemCounter = 0;

// Event Listeners
form.addEventListener('submit', handleFormSubmit);
createMockFeedbackCheckbox.addEventListener('change', toggleMockFeedbackContainer);
addMockItemBtn.addEventListener('click', addMockFeedbackItem);
aiMockButton.addEventListener('click', fillMocksWithAI);

// Initialize
function initialize() {
    // Add one mock item by default when checkbox is checked
    createMockFeedbackCheckbox.addEventListener('change', (e) => {
        if (e.target.checked && mockItemsList.children.length === 0) {
            addMockFeedbackItem();
        }
    });
}

// Toggle Mock Feedback Container
function toggleMockFeedbackContainer() {
    if (createMockFeedbackCheckbox.checked) {
        mockFeedbackContainer.classList.remove('d-none');
        if (mockItemsList.children.length === 0) {
            addMockFeedbackItem();
        }
    } else {
        mockFeedbackContainer.classList.add('d-none');
    }
}

// Auto-fill mock feedback with AI-generated examples
function fillMocksWithAI() {
    // Enable mock feedback checkbox
    createMockFeedbackCheckbox.checked = true;
    toggleMockFeedbackContainer();
    
    // Clear existing mock items
    mockItemsList.innerHTML = '';
    
    // Sample mock data
    const mockData = [
        {
            key: 'UX-101',
            summary: 'Difficult to find the export button',
            description: 'I was trying to export my data but couldn\'t find the button anywhere. After 5 minutes of searching, I found it hidden in a submenu. This should be more prominent.',
            labels: 'feedback, ui, export'
        },
        {
            key: 'UX-102',
            summary: 'Dashboard loads too slowly',
            description: 'The dashboard takes over 10 seconds to load on my computer. This is frustrating when I need to quickly check my stats.',
            labels: 'feedback, performance'
        },
        {
            key: 'UX-103',
            summary: 'Love the new dark mode feature',
            description: 'The dark mode is excellent! It\'s much easier on my eyes when working late at night. Would love to see more customization options though.',
            labels: 'feedback, ui, positive'
        }
    ];
    
    // Add each mock item
    mockData.forEach(data => {
        const item = addMockFeedbackItem();
        
        // Fill in the data
        item.querySelector('.mock-summary').value = data.summary;
        item.querySelector('.mock-description').value = data.description;
        item.querySelector('.mock-ticket-id').value = data.key;
        item.querySelector('.mock-labels').value = data.labels;
    });
    
    // Scroll to the mock items
    mockFeedbackContainer.scrollIntoView({ behavior: 'smooth' });
}

// Modify the addMockFeedbackItem function to return the created item
function addMockFeedbackItem() {
    mockItemCounter++;
    
    // Clone the template
    const template = mockFeedbackItemTemplate.content.cloneNode(true);
    const mockItem = template.querySelector('.mock-feedback-item');
    
    // Set default values
    const ticketIdInput = mockItem.querySelector('.mock-ticket-id');
    ticketIdInput.value = `UX-${100 + mockItemCounter}`;
    
    // Set up remove button
    const removeBtn = mockItem.querySelector('.remove-mock-item');
    removeBtn.addEventListener('click', () => {
        mockItem.remove();
        if (mockItemsList.children.length === 0) {
            // Add back one item if all are removed
            addMockFeedbackItem();
        }
    });
    
    // Add to the list
    mockItemsList.appendChild(mockItem);
    
    return mockItem;
}

// Get mock feedback items
function getMockFeedbackItems() {
    const items = [];
    
    if (!createMockFeedbackCheckbox.checked) {
        return items;
    }
    
    // Collect data from each mock item
    const mockItems = mockItemsList.querySelectorAll('.mock-feedback-item');
    mockItems.forEach(item => {
        const summary = item.querySelector('.mock-summary').value.trim();
        const description = item.querySelector('.mock-description').value.trim();
        const ticketId = item.querySelector('.mock-ticket-id').value.trim();
        const labelsText = item.querySelector('.mock-labels').value.trim();
        
        // Skip if summary is empty
        if (!summary) return;
        
        // Parse labels
        const labels = labelsText ? labelsText.split(',').map(label => label.trim()) : ['feedback'];
        
        items.push({
            key: ticketId || `UX-${100 + items.length + 1}`,
            summary: summary,
            description: description,
            labels: labels
        });
    });
    
    return items;
}

// Functions
async function handleFormSubmit(e) {
    e.preventDefault();
    
    // Get form values
    const jql = jqlInput.value;
    const maxResults = maxResultsInput.value;
    const persistThread = persistThreadCheckbox.checked;
    const postToJira = postToJiraCheckbox.checked;
    const mockFeedbackItems = getMockFeedbackItems();
    
    // Reset UI
    workflowSteps.innerHTML = '';
    resultsContainer.innerHTML = '';
    workflowCard.classList.add('d-none');
    resultsCard.classList.add('d-none');
    
    // Show loading
    showLoading('Initializing agent...');
    
    try {
        // Start the workflow
        const workflowResponse = await fetch('/workflow/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                jql,
                max_results: parseInt(maxResults),
                persist_thread: persistThread,
                post_to_jira: postToJira,
                mock_feedback_items: mockFeedbackItems
            }),
        });
        
        if (!workflowResponse.ok) {
            throw new Error(`Server returned ${workflowResponse.status}`);
        }
        
        const workflowData = await workflowResponse.json();
        currentWorkflowId = workflowData.workflow_id;
        
        // Show workflow card
        workflowCard.classList.remove('d-none');
        
        // Start polling for updates
        await pollWorkflowUpdates();
        
    } catch (error) {
        console.error('Error:', error);
        alert(`Error: ${error.message}`);
        hideLoading();
    }
}

async function pollWorkflowUpdates() {
    if (!currentWorkflowId) return;
    
    try {
        let isComplete = false;
        
        while (!isComplete) {
            // Poll for updates
            const response = await fetch(`/workflow/${currentWorkflowId}/status`);
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            
            const data = await response.json();
            
            // Update UI with new steps
            updateWorkflowSteps(data.steps);
            
            // Update loading message
            showLoading(data.current_status || 'Processing...');
            
            // Check if workflow is complete
            if (data.is_complete) {
                isComplete = true;
                hideLoading();
                
                // Show results
                if (data.results && data.results.length > 0) {
                    displayResults(data.results, data.tickets);
                }
            } else {
                // Wait before polling again
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }
    } catch (error) {
        console.error('Error polling workflow:', error);
        alert(`Error: ${error.message}`);
        hideLoading();
    }
}

function updateWorkflowSteps(steps) {
    // Get only new steps
    const existingStepCount = workflowSteps.querySelectorAll('.workflow-step').length;
    const newSteps = steps.slice(existingStepCount);
    
    // Add new steps to the UI
    newSteps.forEach((step, index) => {
        const stepElement = createWorkflowStepElement(step, existingStepCount + index + 1);
        workflowSteps.appendChild(stepElement);
        stepElement.scrollIntoView({ behavior: 'smooth', block: 'end' });
    });
}

function createWorkflowStepElement(step, number) {
    const template = workflowStepTemplate.content.cloneNode(true);
    const stepElement = template.querySelector('.workflow-step');
    
    // Add fade-in animation
    stepElement.classList.add('fade-in');
    
    // Set step details
    stepElement.querySelector('.step-badge').textContent = `Step ${number}`;
    stepElement.querySelector('.step-title').textContent = step.title;
    stepElement.querySelector('.step-time').textContent = new Date(step.timestamp).toLocaleTimeString();
    
    // Add content based on step type
    const contentElement = stepElement.querySelector('.workflow-step-content');
    
    if (step.type === 'tool_call') {
        // Tool call
        const toolCallEl = document.createElement('div');
        toolCallEl.classList.add('tool-call');
        
        const nameEl = document.createElement('div');
        nameEl.classList.add('tool-call-name');
        nameEl.textContent = `Tool: ${step.tool_name}`;
        toolCallEl.appendChild(nameEl);
        
        const argsEl = document.createElement('div');
        argsEl.classList.add('tool-call-args');
        argsEl.textContent = `Args: ${JSON.stringify(step.args, null, 2)}`;
        toolCallEl.appendChild(argsEl);
        
        if (step.result) {
            const resultEl = document.createElement('div');
            resultEl.classList.add('tool-call-result');
            resultEl.textContent = `Result: ${JSON.stringify(step.result, null, 2)}`;
            toolCallEl.appendChild(resultEl);
        }
        
        contentElement.appendChild(toolCallEl);
    } else {
        // Regular step
        const textElement = document.createElement('p');
        textElement.textContent = step.content || '';
        contentElement.appendChild(textElement);
    }
    
    return stepElement;
}

function displayResults(results, tickets = []) {
    // Map tickets by key for easier lookup
    const ticketMap = {};
    tickets.forEach(ticket => {
        ticketMap[ticket.key] = ticket;
    });
    
    // Show results card
    resultsCard.classList.remove('d-none');
    
    // Create result elements
    results.forEach(result => {
        const resultElement = createResultElement(result, ticketMap[result.ticket_id]);
        resultsContainer.appendChild(resultElement);
    });
}

function createResultElement(result, ticket = null) {
    const template = resultTemplate.content.cloneNode(true);
    const resultElement = template.querySelector('.result-item');
    
    // Set ticket details
    resultElement.querySelector('.ticket-id').textContent = result.ticket_id;
    
    // Set original feedback if available
    if (ticket) {
        resultElement.querySelector('.ticket-summary').textContent = ticket.summary;
        resultElement.querySelector('.ticket-description').textContent = ticket.description || 'No description provided';
    } else {
        resultElement.querySelector('.ticket-summary').textContent = 'Ticket details not available';
        resultElement.querySelector('.ticket-description').textContent = '';
    }
    
    // Set user story
    const userStory = result.user_story;
    resultElement.querySelector('.user-story-title').textContent = userStory.title;
    resultElement.querySelector('.user-story-description').textContent = userStory.description;
    
    // Add acceptance criteria
    const criteriaContainer = resultElement.querySelector('.user-story-criteria');
    userStory.acceptance_criteria.forEach(criterion => {
        const criterionEl = document.createElement('div');
        criterionEl.classList.add('criteria-item');
        criterionEl.textContent = criterion;
        criteriaContainer.appendChild(criterionEl);
    });
    
    // Set PM response
    resultElement.querySelector('.pm-response').textContent = result.pm_response;
    
    // Set up buttons
    const viewJiraBtn = resultElement.querySelector('.view-jira-btn');
    viewJiraBtn.addEventListener('click', () => {
        // Open JIRA ticket in new tab
        const baseUrl = getJiraBaseUrl();
        if (baseUrl) {
            window.open(`${baseUrl}/browse/${result.ticket_id}`, '_blank');
        } else {
            alert('JIRA base URL not configured');
        }
    });
    
    const postCommentBtn = resultElement.querySelector('.post-comment-btn');
    postCommentBtn.addEventListener('click', async () => {
        try {
            showLoading('Posting comment to JIRA...');
            
            const response = await fetch('/jira/post-comment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ticket_id: result.ticket_id,
                    comment: result.pm_response
                }),
            });
            
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            
            const data = await response.json();
            hideLoading();
            
            if (data.success) {
                alert('Comment posted successfully!');
                postCommentBtn.disabled = true;
                postCommentBtn.textContent = 'Posted';
            } else {
                alert(`Error: ${data.message}`);
            }
            
        } catch (error) {
            console.error('Error posting comment:', error);
            alert(`Error: ${error.message}`);
            hideLoading();
        }
    });
    
    return resultElement;
}

function getJiraBaseUrl() {
    // This would ideally come from the server config
    // For now, use a mock URL
    return 'https://your-domain.atlassian.net';
}

function showLoading(message) {
    // Update main loading overlay (now positioned on the left side)
    loadingText.textContent = message;
    loadingOverlay.classList.remove('d-none');
    
    // Update workflow status if workflow card is visible
    if (workflowCard && !workflowCard.classList.contains('d-none')) {
        workflowStatusText.textContent = message;
        workflowStatus.classList.remove('d-none');
        
        // Also update the workflow card header
        const headerEl = workflowCard.querySelector('.card-header');
        if (headerEl) {
            headerEl.innerHTML = `<h4>Agent Workflow</h4>`;
        }
    }
}

function hideLoading() {
    loadingOverlay.classList.add('d-none');
    
    // Also hide workflow status
    if (workflowStatus) {
        workflowStatus.classList.add('d-none');
    }
}

// Initialize the app
initialize(); 