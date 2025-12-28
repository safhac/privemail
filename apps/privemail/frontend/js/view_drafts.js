/**
 * @file view_drafts.js
 * Handles logic for the Inbox/Drafts view.
 */
import * as apiClient from './api_client.js';
import { setupGoalEditor } from './goal_editor.js'; 

let currentContactEmail = null;
let draftGoalEditor = null;

export function renderDraftSidebar(listEl, inboxItems) {
    listEl.innerHTML = '';
    
    const draftCountEl = document.getElementById('stat-drafts');
    if (!inboxItems) {
        listEl.innerHTML = '<p style="padding:20px; color:#666;">Connecting to Privemail Core...</p>';
        draftCountEl.textContent = "...";
        return;
    }
    
    if (inboxItems.length === 0) {
        listEl.innerHTML = '<p style="padding:20px;">Inbox is empty.</p>';
        draftCountEl.textContent = "0";
        return;
    }
    
    draftCountEl.textContent = inboxItems.length;

    inboxItems.forEach(item => {
        const li = document.createElement('li');
        li.className = 'inbox-item';
        
        if (item.local_priority_score > 50) li.style.borderLeft = "4px solid #ff4444";
        else if (item.local_priority_score > 20) li.style.borderLeft = "4px solid #ffbb33";
        
        li.innerHTML = `
            <div class="inbox-item-email">
                <strong>${item.correspondent}</strong>
                <span class="subject">${item.subject}</span>
            </div>
        `;
        
        if (item.has_draft) {
            const status = item.draft_status === 'pending' ? 'Pending' : `Draft ${item.draft_id}`;
            li.innerHTML += `<div class="inbox-item-draft">└ ${status}</div>`;
            li.style.cursor = 'pointer';
            li.onclick = () => handleDraftSelection(item.draft_id, li);
        } else {
            li.innerHTML += `<div class="inbox-item-draft" style="color: #999;">(No Draft - Auto-skipped)</div>`;
            li.classList.add('no-draft');
        }
        
        listEl.appendChild(li);
    });
}

async function handleDraftSelection(draftId, liElement) {
    document.querySelectorAll('#sidebar-list li').forEach(l => l.classList.remove('selected'));
    liElement.classList.add('selected');
    
    document.getElementById('view-contacts').style.display = 'none';
    document.getElementById('view-drafts').style.display = 'block';
    document.getElementById('right-panel-drafts').style.display = 'block';

    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    const activeLink = document.querySelector(`.nav-link[data-view="drafts"]`);
    if(activeLink) activeLink.classList.add('active');

    document.getElementById('draft-detail-container').style.display = 'block';
    document.getElementById('draft-placeholder').style.display = 'none';
    document.getElementById('original-email-body').textContent = 'Loading...';
    document.getElementById('draft-text-area').textContent = 'Loading...';
    
    const draftDetail = await apiClient.fetchDraftDetail(draftId);
    if(draftDetail) {
        currentContactEmail = parseEmailFromSender(draftDetail.original_sender);
        const contactDetail = await apiClient.fetchContactDetail(currentContactEmail);
        
        renderDraftDetail(draftDetail, contactDetail);
        wireAudioLock(draftDetail.draft_id, draftDetail.is_read_and_confirmed);
        wireAiControls(draftDetail.draft_id, currentContactEmail, contactDetail);
        wireSendButton(draftDetail.draft_id, draftDetail.status);
    }
}

function renderDraftDetail(draftDetail, contactDetail) {
    document.getElementById('draft-subject').textContent = draftDetail.original_subject;
    document.getElementById('draft-recipient').textContent = draftDetail.original_sender;
    document.getElementById('original-email-body').textContent = draftDetail.original_body;
    
    const draftTextArea = document.getElementById('draft-text-area');
    
    // --- FEATURE: Manual Mode UI ---
    if (draftDetail.status === 'pending') {
        draftTextArea.innerHTML = `
            <div style="text-align: center; padding: 30px; background: #f3f4f6; border-radius: 8px;">
                <p style="color: #666; margin-bottom: 15px;">Draft generation is pending (Manual Mode).</p>
                <button id="btn-manual-generate" style="padding: 10px 20px; background: #2563eb; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    ✨ Generate Draft Now
                </button>
            </div>
        `;
        draftTextArea.contentEditable = "false";
        draftTextArea.style.backgroundColor = "transparent";
        draftTextArea.style.border = "none";
        
        // Wire up the generate button
        setTimeout(() => {
            const btn = document.getElementById('btn-manual-generate');
            if(btn) {
                btn.onclick = async function() {
                    this.textContent = "Generating... (Please Wait)";
                    this.disabled = true;
                    try {
                        await apiClient.generateDraftManually(draftDetail.draft_id);
                        // Refresh view
                        const li = document.querySelector('#sidebar-list li.selected');
                        handleDraftSelection(draftDetail.draft_id, li);
                    } catch(e) {
                        this.textContent = "Error";
                        alert("Generation failed.");
                    }
                };
            }
        }, 0);
        
        document.getElementById('send-button').disabled = true;
        return; 
    } 
    
    // --- FEATURE: Editable Drafts ---
    draftTextArea.textContent = draftDetail.generated_text;
    draftTextArea.contentEditable = "true"; 
    draftTextArea.style.border = "1px dashed #ccc"; 
    draftTextArea.style.padding = "10px";
    
    if (draftDetail.status === 'sent') {
        draftTextArea.style.backgroundColor = "#f0f0f0";
        draftTextArea.style.color = "#666";
        draftTextArea.contentEditable = "false";
        draftTextArea.style.border = "none";
        
        if (!document.getElementById('sent-banner')) {
             const banner = document.createElement('div');
             banner.id = 'sent-banner';
             banner.textContent = "✓ This email has been replied to.";
             banner.style.cssText = "background:#d1fae5; color:#065f46; padding:10px; border-radius:4px; margin-bottom:10px; font-weight:bold;";
             draftTextArea.parentNode.insertBefore(banner, draftTextArea);
        }
    } else {
         draftTextArea.style.backgroundColor = "#fff";
         draftTextArea.style.color = "#333";
         const banner = document.getElementById('sent-banner');
         if(banner) banner.remove();
    }
    
    const whyLink = document.getElementById('why-analysis-link');
    if(whyLink && draftDetail.correspondent_evidence) {
        whyLink.style.display = 'inline';
        whyLink.onclick = (e) => {
            e.preventDefault();
            alert(`AI Analysis:\nTone: ${draftDetail.correspondent_tone}\nEvidence: "${draftDetail.correspondent_evidence}"`);
        }
    }

    const emailDisplay = contactDetail && contactDetail.name ? `${contactDetail.name} (${contactDetail.email_address})` : currentContactEmail;
    document.getElementById('contact-info-email').textContent = emailDisplay;

    if (!draftGoalEditor) {
        draftGoalEditor = setupGoalEditor('goal-input-container');
    }
    const goalText = (contactDetail && contactDetail.goal) || "Provide information";
    if (draftGoalEditor) {
        draftGoalEditor.setValue(goalText);
    }
    
    const toneSelect = document.getElementById('tone-select');
    const savedTone = (contactDetail && contactDetail.tone) ? contactDetail.tone : "professional";
    if (!Array.from(toneSelect.options).some(opt => opt.value === savedTone)) {
        const newOption = new Option(savedTone, savedTone, true, true);
        toneSelect.add(newOption);
    }
    toneSelect.value = savedTone;

    const savedStrength = (contactDetail && typeof contactDetail.tone_strength === 'number') ? contactDetail.tone_strength : 0.5;
    document.getElementById('tone-dial-slider').value = savedStrength;
    document.getElementById('tone-dial-value').textContent = savedStrength;

    const sendButton = document.getElementById('send-button');
    const lockButton = document.getElementById('audio-lock-button');

    if (draftDetail.is_read_and_confirmed) {
        sendButton.disabled = false;
        lockButton.disabled = true;
        lockButton.textContent = 'Confirmed';
    } else {
        sendButton.disabled = true;
        lockButton.disabled = false;
        lockButton.textContent = 'Confirm Read (Simulated Listen)';
    }
}

function wireAudioLock(draftId, isConfirmed) {
    const btn = document.getElementById('audio-lock-button');
    const newBtn = btn.cloneNode(true);
    btn.parentNode.replaceChild(newBtn, btn);
    
    if(isConfirmed) return;
    
    newBtn.onclick = async () => {
        newBtn.textContent = 'Confirming...';
        try {
            await apiClient.confirmDraftRead(draftId);
            newBtn.textContent = "Confirmed";
            newBtn.disabled = true;
            document.getElementById('send-button').disabled = false;
        } catch (e) {
            alert("Failed to confirm.");
            newBtn.textContent = 'Confirm Read (Simulated Listen)';
        }
    };
}

function wireSendButton(draftId, status) {
    const btn = document.getElementById('send-button');
    const newBtn = btn.cloneNode(true);
    btn.parentNode.replaceChild(newBtn, btn);

    if (status === 'sent') {
        newBtn.textContent = "Sent";
        newBtn.disabled = true;
        newBtn.style.backgroundColor = "#6b7280";
        return;
    }

    newBtn.onclick = async () => {
        const isDirectSend = document.getElementById('direct-send-toggle').checked;
        const mode = isDirectSend ? "send" : "draft";
        
        let confirmMsg = isDirectSend ? 
            "⚠️ WARNING: Sending directly. Proceed?" : 
            "Create a draft in Gmail?";

        if(!confirm(confirmMsg)) return;
        
        newBtn.textContent = "Processing...";
        newBtn.disabled = true;
        
        try {
            // --- FEATURE: Auto-Save Edits Before Sending ---
            const currentText = document.getElementById('draft-text-area').innerText;
            await apiClient.updateDraftText(draftId, currentText);
            // -----------------------------------------------

            await apiClient.sendDraft(draftId, mode);
            newBtn.textContent = isDirectSend ? "Sent!" : "Draft Created!";
            newBtn.style.backgroundColor = "#6b7280"; 
            
            const draftTextArea = document.getElementById('draft-text-area');
            draftTextArea.style.backgroundColor = "#f0f0f0";
            draftTextArea.contentEditable = "false";
            
        } catch (e) {
            console.error(e);
            alert("Failed to process request.");
            newBtn.textContent = "Send";
            newBtn.disabled = false;
        }
    };
}

function wireAiControls(draftId, email, contactDetail) {
    const slider = document.getElementById('tone-dial-slider');
    const display = document.getElementById('tone-dial-value');
    slider.oninput = () => display.textContent = slider.value;

    const btnRewrite = document.getElementById('rewrite-button');
    const newRewrite = btnRewrite.cloneNode(true);
    btnRewrite.parentNode.replaceChild(newRewrite, btnRewrite);
    
    newRewrite.onclick = async () => {
        newRewrite.disabled = true;
        newRewrite.textContent = "Rewriting...";
        try {
            const text = await apiClient.sendRewriteRequest(
                draftId,
                document.getElementById('draft-text-area').textContent,
                draftGoalEditor ? draftGoalEditor.getValue() : "", 
                document.getElementById('tone-select').value,
                parseFloat(slider.value),
                document.getElementById('ad-hoc-input').value,
                document.getElementById('model-select-dropdown').value
            );
            document.getElementById('draft-text-area').textContent = text;
        } catch(e) {
            console.error(e);
            alert("Rewrite failed.");
        } finally {
            newRewrite.disabled = false;
            newRewrite.textContent = "Rewrite";
        }
    };
    
    const btnSave = document.getElementById('save-contact-prefs-button');
    const newSave = btnSave.cloneNode(true);
    btnSave.parentNode.replaceChild(newSave, btnSave);
    
    newSave.onclick = async () => {
        newSave.textContent = "Saving...";
        try {
            const selectedModel = document.getElementById('model-select-dropdown').value;
            
            await Promise.all([
                apiClient.updateContact({
                    email_address: email,
                    goal: draftGoalEditor ? draftGoalEditor.getValue() : "",
                    tone: document.getElementById('tone-select').value,
                    tone_strength: parseFloat(slider.value),
                    name: contactDetail ? contactDetail.name : null,
                    contact_group: contactDetail ? contactDetail.contact_group : null
                }),
                apiClient.updateSelectedModel(selectedModel)
            ]);

            newSave.textContent = "Saved!";
            setTimeout(() => newSave.textContent = "Save Preferences", 1500);
        } catch(e) {
            console.error(e);
            alert("Failed to save preferences.");
            newSave.textContent = "Save Preferences";
        }
    };
}

function parseEmailFromSender(str) {
    const match = str && str.match(/<(.+?)>/);
    return match ? match[1] : (str || "");
}