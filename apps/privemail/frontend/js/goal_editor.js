/**
 * @file goal_editor.js
 * Reusable logic for the "Command Module" style Goal Editor.
 */

export function setupGoalEditor(containerId, initialValue = "") {
    const container = document.getElementById(containerId);
    if (!container) return null;

    // 1. Inject HTML Structure
    container.innerHTML = `
        <div class="goal-editor-wrapper">
            <div class="goal-editor-toolbar">
                <span style="font-size:0.75em; color:#888; margin-right:auto; align-self:center;">Insert Guide:</span>
                <button class="tag-helper-btn" data-tag="[Persona]">[Persona]</button>
                <button class="tag-helper-btn" data-tag="[Action]">[Action]</button>
                <button class="tag-helper-btn" data-tag="[Constraint]">[Constraint]</button>
                <button class="tag-helper-btn" data-tag="[Context]">[Context]</button>
            </div>
            <div class="goal-editor-content" contenteditable="true"></div>
        </div>
    `;

    const wrapper = container.querySelector('.goal-editor-wrapper');
    const editor = container.querySelector('.goal-editor-content');
    const toolbar = container.querySelector('.goal-editor-toolbar');

    // 2. Helper: Formatting Text (Coloring)
    const renderFormatted = () => {
        const text = editor.innerText; 
        // Regex to find [Tags] and wrap them in span
        // We use a temp div to safely encode HTML entities first if needed
        // For simplicity in vanilla JS without XSS risk on local app:
        const formatted = text.replace(/(\[.*?\])/g, '<span class="goal-tag" contenteditable="false">$1</span>');
        editor.innerHTML = formatted;
    };

    // 3. Helper: Set Value (Safe way to set initial text)
    const setValue = (text) => {
        editor.innerText = text || "";
        renderFormatted();
    };

    // 4. Event Listeners
    
    // Focus: Add 'expanded' class, clear formatting to plain text for easy editing
    editor.addEventListener('focus', () => {
        wrapper.classList.add('expanded');
        // Optional: If you prefer editing plain text, you can strip tags here.
        // For now, we keep tags but user can delete them.
    });

    // Blur: Remove 'expanded', Re-apply formatting
    editor.addEventListener('blur', (e) => {
        // Delay collapse slightly to allow button clicks in toolbar
        if (!wrapper.contains(e.relatedTarget)) {
            wrapper.classList.remove('expanded');
            renderFormatted();
        }
    });

    // Toolbar Clicks
    toolbar.querySelectorAll('.tag-helper-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const tag = btn.getAttribute('data-tag');
            insertTextAtCursor(tag + " ");
            editor.focus(); // Keep focus
        });
    });
    
    // Helper to insert at cursor position
    function insertTextAtCursor(text) {
        const selection = window.getSelection();
        if (!selection.rangeCount) return;
        const range = selection.getRangeAt(0);
        range.deleteContents();
        const textNode = document.createTextNode(text);
        range.insertNode(textNode);
        // Move cursor after text
        range.setStartAfter(textNode);
        range.setEndAfter(textNode); 
        selection.removeAllRanges();
        selection.addRange(range);
    }

    // Set initial value
    setValue(initialValue);

    // 5. Return Interface for other modules to use
    return {
        getValue: () => editor.innerText, // Always return plain text for API
        setValue: setValue
    };
}