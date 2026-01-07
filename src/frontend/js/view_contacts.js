/**
 * @file view_contacts.js
 * Handles logic for the Contacts and Groups split-view.
 */
import * as apiClient from './api_client.js';
import { setupGoalEditor } from './goal_editor.js';

export const DEFAULT_GOAL_TEMPLATE = "My goal is to [ACTION] regarding [TOPIC]. I want to ensure that [OUTCOME]. Please maintain a [TONE] tone.";
export const GROUP_GOAL_TEMPLATE = "We represent the [Team Name]. Our objective is to [Objective] regarding [Project]. Ensure we sound [Adjective] and unified.";

let _switchViewCallback = null;
let allGroups = []; 
let contactGoalEditor = null;
let groupGoalEditor = null; // New Editor for Groups

export function setSwitchViewCallback(cb) {
    _switchViewCallback = cb;
}

// --- INITIALIZATION ---
export async function initContactsView() {
    const [contacts, groups] = await Promise.all([
        apiClient.fetchContactsList(),
        apiClient.fetchGroups()
    ]);
    allGroups = groups || [];
    
    renderGroupsTable(allGroups);
    renderContactsTable(contacts);
    
    // Wire up "Add Group"
    const btnAddGroup = document.getElementById('btn-add-group');
    const newBtnAddGroup = btnAddGroup.cloneNode(true);
    btnAddGroup.parentNode.replaceChild(newBtnAddGroup, btnAddGroup);
    
    newBtnAddGroup.onclick = async () => {
        const nameInput = document.getElementById('new-group-name');
        const colorInput = document.getElementById('new-group-color');
        const name = nameInput.value.trim();
        
        if(!name) {
            alert("Please enter a group name.");
            return;
        }

        newBtnAddGroup.textContent = "Adding...";
        newBtnAddGroup.disabled = true;

        try {
            await apiClient.createGroup({ name: name, color: colorInput.value });
            await initContactsView(); // Refresh table
            document.getElementById('new-group-name').value = '';
        } catch(e) {
            console.error(e);
            alert("Failed to add group. Name might be duplicate.");
        } finally {
            newBtnAddGroup.textContent = "Add Group";
            newBtnAddGroup.disabled = false;
        }
    };

    // Wire up "Add Contact"
    const btnAddContact = document.getElementById('btn-add-contact');
    const newBtnAddContact = btnAddContact.cloneNode(true);
    btnAddContact.parentNode.replaceChild(newBtnAddContact, btnAddContact);
    
    newBtnAddContact.onclick = () => {
       const email = prompt("Enter email for new contact:");
       if(email) {
           apiClient.updateContact({ email_address: email }).then(() => initContactsView());
       }
    };

    // --- IMPORT BUTTONS ---
    // FIXED: Find the new specific actions container in the card header
    const actionsContainer = document.getElementById('contacts-header-actions');
    
    if (actionsContainer && !document.getElementById('btn-import-google')) {
        
        // Google Import
        const btnGoogle = document.createElement('button');
        btnGoogle.id = 'btn-import-google';
        btnGoogle.textContent = 'G';
        btnGoogle.title = "Sync from Google Contacts";
        btnGoogle.className = 'icon-btn';
        btnGoogle.style.backgroundColor = '#DB4437';
        btnGoogle.style.color = 'white';
        btnGoogle.style.width = '32px';
        btnGoogle.style.height = '32px';
        
        btnGoogle.onclick = async () => {
            if(!confirm("Sync contacts from Google? This may take a moment.")) return;
            btnGoogle.textContent = '...';
            try {
                const res = await apiClient.importGoogleContacts();
                alert(`Imported ${res.imported_count} new contacts.`);
                initContactsView(); 
            } catch(e) {
                console.error(e);
                alert("Import failed. You may need to Re-Auth Google in Settings.");
            } finally {
                btnGoogle.textContent = 'G';
            }
        };

        // VCF Import
        const btnVcf = document.createElement('button');
        btnVcf.id = 'btn-import-vcf';
        btnVcf.textContent = '📱';
        btnVcf.title = "Import .vcf (Phone)";
        btnVcf.className = 'icon-btn';
        btnVcf.style.backgroundColor = '#2563eb';
        btnVcf.style.color = 'white';
        btnVcf.style.width = '32px';
        btnVcf.style.height = '32px';
        
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = '.vcf';
        fileInput.style.display = 'none';
        
        btnVcf.onclick = () => fileInput.click();
        
        fileInput.onchange = async (e) => {
            if(e.target.files.length > 0) {
                btnVcf.textContent = '...';
                try {
                    const res = await apiClient.uploadVCard(e.target.files[0]);
                    alert(`Imported ${res.imported_count} contacts from file.`);
                    initContactsView();
                } catch(e) {
                    console.error(e);
                    alert("Failed to parse file.");
                } finally {
                    btnVcf.textContent = '📱';
                    fileInput.value = ''; 
                }
            }
        };

        // Insert buttons *before* the Add button in the flex container
        actionsContainer.insertBefore(fileInput, btnAddContact);
        actionsContainer.insertBefore(btnVcf, btnAddContact);
        actionsContainer.insertBefore(btnGoogle, btnAddContact);
    }
}

// --- GROUPS TABLE ---
function renderGroupsTable(groups) {
    const tbody = document.querySelector('#groups-table tbody');
    tbody.innerHTML = '';
    
    groups.forEach(g => {
        const tr = document.createElement('tr');
        
        // Create the color dot
        const colorDot = `<span style="display:inline-block; width:12px; height:12px; background-color:${g.color || '#ccc'}; border-radius:50%; margin-right:8px;"></span>`;
        
        tr.innerHTML = `
            <td>${colorDot} <strong>${g.name}</strong></td>
            <td style="color:#666;">${g.color || '#ffffff'}</td>
            <td style="max-width: 250px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${g.group_goal || '<em style="color:#999">No strategy set</em>'}</td>
            <td>${g.group_tone || '-'}</td>
            <td>
                <button class="btn-sm btn-edit-group">Edit Strategy</button>
            </td>
        `;
        
        const editBtn = tr.querySelector('.btn-edit-group');
        editBtn.onclick = () => handleGroupSelection(g);
        
        tbody.appendChild(tr);
    });
}

// --- CONTACTS TABLE ---
function renderContactsTable(contacts) {
    const tbody = document.querySelector('#contacts-table tbody');
    tbody.innerHTML = '';
    contacts.forEach(c => {
        const tr = document.createElement('tr');
        
        const group = allGroups.find(g => g.id === c.group_id);
        if(group && group.color) {
            tr.style.backgroundColor = group.color + '33'; 
        }
        
        tr.innerHTML = `
            <td>${c.name || ''}</td>
            <td>${c.email_address}</td>
            <td>${group ? group.name : '-'}</td>
            <td style="max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${c.goal || ''}</td>
            <td><button class="btn-sm btn-edit">Edit</button></td>
        `;
        
        const editBtn = tr.querySelector('.btn-edit');
        editBtn.onclick = (e) => {
            e.stopPropagation();
            handleContactSelection(c);
        };
        tr.onclick = () => handleContactSelection(c);
        
        tbody.appendChild(tr);
    });
}

// --- NEW: GROUP EDITOR LOGIC ---
function handleGroupSelection(group) {
    const editorOverlay = document.getElementById('group-editor');
    if (!editorOverlay) return;
    
    editorOverlay.style.display = 'block';
    
    // Populate Fields
    document.getElementById('editor-group-name').value = group.name;
    document.getElementById('editor-group-color').value = group.color || "#ffffff";
    document.getElementById('editor-group-tone').value = group.group_tone || 'professional';
    
    const strength = group.group_urgency || 0.5; // Mapping urgency to tone strength for groups
    document.getElementById('editor-group-tone-strength').value = strength;
    document.getElementById('group-tone-val').textContent = strength;

    // Initialize Goal Editor
    if (!groupGoalEditor) {
        groupGoalEditor = setupGoalEditor('editor-group-goal-container');
    }
    groupGoalEditor.setValue(group.group_goal || '');

    // Wire up Template Button
    document.getElementById('btn-group-template').onclick = () => {
        groupGoalEditor.setValue(GROUP_GOAL_TEMPLATE);
    };

    // Wire up Save Button
    const btnSave = document.getElementById('btn-save-group');
    const newBtn = btnSave.cloneNode(true);
    btnSave.parentNode.replaceChild(newBtn, btnSave);

    newBtn.onclick = async () => {
        newBtn.textContent = "Saving Strategy...";
        const updatedGroup = {
            name: group.name, // Name acts as ID in backend
            color: document.getElementById('editor-group-color').value,
            group_goal: groupGoalEditor.getValue(),
            group_tone: document.getElementById('editor-group-tone').value,
            group_urgency: parseFloat(document.getElementById('editor-group-tone-strength').value)
        };
        
        try {
            await apiClient.createGroup(updatedGroup);
            newBtn.textContent = "Saved!";
            setTimeout(() => {
                newBtn.textContent = "Save Group Strategy";
                editorOverlay.style.display = 'none';
                initContactsView(); // Refresh table
            }, 1000);
        } catch(e) {
            console.error(e);
            alert("Failed to save group.");
            newBtn.textContent = "Save Group Strategy";
        }
    };
}

// --- CONTACT EDITOR LOGIC ---
async function handleContactSelection(contact) {
    const editorOverlay = document.getElementById('contact-editor');
    if (editorOverlay) {
        editorOverlay.style.display = 'block';
    } else {
        return;
    }
    
    document.getElementById('editor-email').value = contact.email_address;
    document.getElementById('editor-name').value = contact.name || '';
    
    if (!contactGoalEditor) {
        contactGoalEditor = setupGoalEditor('editor-goal-container');
    }
    if (contactGoalEditor) {
        contactGoalEditor.setValue(contact.goal || '');
    }

    document.getElementById('editor-tone').value = contact.tone || 'professional';
    document.getElementById('editor-tone-strength').value = contact.tone_strength || 0.5;
    document.getElementById('editor-auto-draft').checked = contact.auto_draft_enabled;

    const groupSelect = document.getElementById('editor-group');
    groupSelect.innerHTML = '<option value="">None</option>';
    allGroups.forEach(g => {
        const opt = new Option(g.name, g.id);
        if(contact.group_id === g.id) opt.selected = true;
        groupSelect.add(opt);
    });

    const btnSave = document.getElementById('btn-save-contact');
    const newBtn = btnSave.cloneNode(true);
    btnSave.parentNode.replaceChild(newBtn, btnSave);
    newBtn.onclick = async () => {
        newBtn.textContent = 'Saving...';
        const updatedData = {
            email_address: contact.email_address,
            name: document.getElementById('editor-name').value,
            group_id: document.getElementById('editor-group').value || null,
            goal: contactGoalEditor ? contactGoalEditor.getValue() : "", 
            tone: document.getElementById('editor-tone').value,
            tone_strength: parseFloat(document.getElementById('editor-tone-strength').value),
            auto_draft_enabled: document.getElementById('editor-auto-draft').checked
        };
        try {
            await apiClient.updateContact(updatedData);
            newBtn.textContent = 'Saved!';
            setTimeout(() => {
                newBtn.textContent = 'Save Contact';
                editorOverlay.style.display = 'none'; 
            }, 1000);
            initContactsView();
        } catch (e) {
            console.error(e);
            alert("Failed to update contact.");
            newBtn.textContent = 'Save Contact';
        }
    };

    const btnDefault = document.getElementById('btn-set-default-goal');
    btnDefault.onclick = () => {
        if(contactGoalEditor) contactGoalEditor.setValue(DEFAULT_GOAL_TEMPLATE);
    };
    const btnReset = document.getElementById('btn-reset-goal');
    btnReset.onclick = () => {
        if(contactGoalEditor) contactGoalEditor.setValue('');
    };

    const btnManage = document.getElementById('btn-manage-groups');
    const newManage = btnManage.cloneNode(true);
    btnManage.parentNode.replaceChild(newManage, btnManage);
    newManage.onclick = async () => {
        const name = prompt("Enter name for new Group:");
        if(name) {
            try {
                await apiClient.createGroup({ name: name });
                const newGroups = await apiClient.fetchGroups();
                allGroups = newGroups; 
                groupSelect.innerHTML = '<option value="">None</option>';
                newGroups.forEach(g => groupSelect.add(new Option(g.name, g.id)));
            } catch (e) {
                alert("Failed to create group.");
            }
        }
    };
}