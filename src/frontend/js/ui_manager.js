import * as apiClient from './api_client.js';
import * as draftView from './view_drafts.js';
import * as contactView from './view_contacts.js';
import * as settingsView from './view_settings.js';

export async function initializeUI() {
    console.log("UI Manager: Initializing...");
    
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            // Handle click on icon span vs link anchor
            const target = e.target.closest('.nav-link');
            if (target) {
                switchView(target.dataset.view);
            }
        });
    });

    // Initial Load
    switchView('drafts');
    
    // Fetch Models AND Settings to set the default model correctly
    try {
        const [models, settings] = await Promise.all([
            apiClient.fetchModelList(),
            apiClient.fetchSettings()
        ]);

        renderModelDropdown(
            document.getElementById('model-select-dropdown'), 
            models,
            settings ? settings.ollama_model : null
        );
    } catch (error) {
        console.error("Failed to initialize UI data:", error);
    }
}

async function switchView(viewName) {
    // 1. Update Navigation State
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    const activeLink = document.querySelector(`.nav-link[data-view="${viewName}"]`);
    if(activeLink) activeLink.classList.add('active');

    // 2. Hide All Views
    document.getElementById('view-drafts').style.display = 'none';
    document.getElementById('view-contacts').style.display = 'none';
    document.getElementById('view-settings').style.display = 'none';
    document.getElementById('right-panel-drafts').style.display = 'none';

    // 3. Show Selected View
    if (viewName === 'drafts') {
        document.getElementById('view-drafts').style.display = 'block';
        document.getElementById('right-panel-drafts').style.display = 'block';
        
        // Update Status Bar
        const draftStat = document.getElementById('stat-drafts');
        draftStat.textContent = '...'; 
        
        try {
            const inboxItems = await apiClient.fetchInboxList();
            draftStat.textContent = inboxItems ? inboxItems.length : 0;
            draftView.renderDraftSidebar(document.getElementById('sidebar-list'), inboxItems);
        } catch (e) {
            console.error("Error loading inbox:", e);
            draftStat.textContent = "Err";
        }
    } 
    else if (viewName === 'contacts') {
        document.getElementById('view-contacts').style.display = 'block';
        document.getElementById('right-panel-drafts').style.display = 'none';
        
        // Initialize the contact table view
        contactView.initContactsView();
    }
    else if (viewName === 'settings') {
        document.getElementById('view-settings').style.display = 'block';
        document.getElementById('right-panel-drafts').style.display = 'none';

        // Render settings form
        const settingsContainer = document.getElementById('view-settings');
        settingsView.renderSettingsView(settingsContainer);
    }
}

function renderModelDropdown(el, models, savedModel) {
    if(!el || !models) return;
    el.innerHTML = '';
    
    let foundSaved = false;

    models.forEach(m => {
        const opt = new Option(m, m);
        if (m === savedModel) {
            opt.selected = true;
            foundSaved = true;
        }
        el.add(opt);
    });

    // If the saved model wasn't found in the list (or is null), default to first one
    if (!foundSaved && models.length > 0) {
        el.value = models[0];
    }

    // Auto-save when the user changes the dropdown directly
    el.onchange = async () => {
        console.log(`Auto-saving model preference: ${el.value}`);
        try {
            await apiClient.updateSelectedModel(el.value);
        } catch (e) {
            console.error("Failed to save model preference:", e);
            alert("Failed to save default model.");
        }
    };
}

document.addEventListener('DOMContentLoaded', initializeUI);