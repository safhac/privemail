/**
 * @file api_client.js
 * Handles all network communication with the FastAPI backend.
 */

const API_BASE_URL = "/api";

async function fetchAPI(url, options = {}) {
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            if (response.status === 404) return null;
            const errorText = await response.text();
            throw new Error(`API Error: ${response.status} ${response.statusText} - ${errorText}`);
        }

        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("text/plain")) return response.text();
        if (response.status === 204 || !contentType || !contentType.includes("application/json")) return null;
        
        return response.json();
    } catch (error) {
        console.error(`Failed to fetch ${url}`, error);
        throw error;
    }
}

export async function fetchInboxList(page = 1) {
    return fetchAPI(`${API_BASE_URL}/inbox/?page=${page}`);
}

export async function fetchModelList() {
    return fetchAPI(`${API_BASE_URL}/models`);
}

export async function fetchDraftDetail(draftId) {
    return fetchAPI(`${API_BASE_URL}/drafts/${draftId}`);
}

export async function fetchContactDetail(email) {
    return fetchAPI(`${API_BASE_URL}/contacts/${encodeURIComponent(email)}`);
}

export async function fetchContactsList() {
    return fetchAPI(`${API_BASE_URL}/contacts/`);
}

export async function updateContact(contactData) {
    return fetchAPI(`${API_BASE_URL}/contacts/`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(contactData)
    });
}

export async function fetchGroups() {
    return fetchAPI(`${API_BASE_URL}/groups/`);
}

export async function createGroup(groupData) {
    return fetchAPI(`${API_BASE_URL}/groups/`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(groupData)
    });
}

export async function fetchSettings() {
    return fetchAPI(`${API_BASE_URL}/settings`);
}

export async function updateSelectedModel(modelName) {
    return fetchAPI(`${API_BASE_URL}/settings/model`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ model_name: modelName })
    });
}

export async function sendRewriteRequest(draftId, paragraphText, goal, tone, dialValue, instruction, model) {
    const body = {
        paragraph: paragraphText, goal: goal, tone: tone, tone_dial_value: dialValue,
        ad_hoc_instruction: instruction, model: model
    };
    return fetchAPI(`${API_BASE_URL}/drafts/${draftId}/rewrite`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body)
    });
}

export async function confirmDraftRead(draftId) {
    return fetchAPI(`${API_BASE_URL}/drafts/${draftId}/confirm`, { method: 'POST' });
}

export async function sendDraft(draftId, mode = "draft") {
    return fetchAPI(`${API_BASE_URL}/drafts/${draftId}/send?mode=${mode}`, {
        method: 'POST'
    });
}

export async function generateDraftManually(draftId) {
    return fetchAPI(`${API_BASE_URL}/drafts/${draftId}/generate`, { method: 'POST' });
}

export async function updateDraftText(draftId, newText) {
    return fetchAPI(`${API_BASE_URL}/drafts/${draftId}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ final_text: newText })
    });
}

// --- NEW: Import Functions ---

export async function importGoogleContacts() {
    return fetchAPI(`${API_BASE_URL}/contacts/import/google`, { method: 'POST' });
}

export async function uploadVCard(fileObject) {
    const formData = new FormData();
    formData.append('file', fileObject);
    
    // Note: We don't use fetchAPI here because we must let the browser 
    // set the Content-Type (and boundary) for FormData automatically.
    const response = await fetch(`${API_BASE_URL}/contacts/import/vcard`, {
        method: 'POST',
        body: formData
    });
    
    if (!response.ok) {
        const err = await response.text();
        throw new Error(`Upload failed: ${err}`);
    }
    return response.json();
}