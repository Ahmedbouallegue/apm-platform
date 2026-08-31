/**
 * APM Platform — Chatbot IA DSI
 * Gère le widget flottant ET la page dédiée
 */

/* ══════════════════════════════════════════════════════════════
   WIDGET FLOTTANT
══════════════════════════════════════════════════════════════ */

function initChatbotWidget() {
  const config = window.APM_CHATBOT_CONFIG || {};
  if (!config.askUrl) return;

  // Injecter le HTML du widget dans le DOM
  const widgetHTML = `
    <button class="chatbot-fab" id="chatbotFab" aria-label="Ouvrir l'assistant IA" title="Assistant IA DSI">
      <svg class="fab-icon-open" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
        <path d="M12 2a4 4 0 0 1 4 4v1h1a3 3 0 0 1 3 3v8a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3v-8a3 3 0 0 1 3-3h1V6a4 4 0 0 1 4-4z"/>
        <circle cx="9" cy="11" r="1" fill="currentColor"/>
        <circle cx="15" cy="11" r="1" fill="currentColor"/>
        <path d="M9 16s1 1 3 1 3-1 3-1"/>
      </svg>
      <svg class="fab-icon-close" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M18 6L6 18M6 6l12 12"/>
      </svg>
    </button>

    <div class="chatbot-panel" id="chatbotPanel" role="dialog" aria-label="Assistant IA DSI">
      <!-- Header -->
      <div class="chatbot-panel-header">
        <div class="chat-ai-avatar">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <path d="M12 2a4 4 0 0 1 4 4v1h1a3 3 0 0 1 3 3v8a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3v-8a3 3 0 0 1 3-3h1V6a4 4 0 0 1 4-4z"/>
            <circle cx="9" cy="11" r="1" fill="currentColor"/>
            <circle cx="15" cy="11" r="1" fill="currentColor"/>
            <path d="M9 16s1 1 3 1 3-1 3-1"/>
          </svg>
        </div>
        <div class="chatbot-panel-header-info">
          <p class="chatbot-panel-title">Assistant DSI IA</p>
          <p class="chatbot-panel-subtitle">Gemini 2.0 Flash · Topnet APM</p>
        </div>
        <div style="display:flex;align-items:center;gap:8px">
          <span class="chatbot-panel-status">En ligne</span>
          <a href="${config.chatPageUrl || '/chatbot/'}" class="chatbot-expand-link" title="Ouvrir en pleine page">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/>
            </svg>
          </a>
          <button class="chatbot-panel-btn" id="chatbotClearBtn" title="Effacer la conversation">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- Messages -->
      <div class="widget-messages" id="widgetMessages">
        <div class="chat-message chat-message--ai">
          <div class="chat-bubble chat-bubble--ai">
            <div class="chat-bubble-header">
              <span class="chat-bubble-sender">🤖 Assistant DSI</span>
            </div>
            <div class="chat-bubble-content">
              Bonjour ! Je suis votre assistant IA.<br>
              Posez-moi vos questions sur le patrimoine applicatif Topnet 👋
            </div>
          </div>
        </div>
      </div>

      <!-- Input -->
      <div class="widget-input-zone">
        <div class="widget-input-row">
          <textarea
            id="widgetInput"
            class="widget-textarea"
            placeholder="Votre question..."
            rows="1"
            maxlength="2000"
          ></textarea>
          <button id="widgetSendBtn" class="widget-send-btn" disabled>
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z"/>
            </svg>
          </button>
        </div>
        <p class="widget-hint">Entrée pour envoyer · Maj+Entrée pour saut de ligne</p>
      </div>
    </div>
  `;

  const container = document.createElement('div');
  container.innerHTML = widgetHTML;
  document.body.appendChild(container);

  // Initialiser les interactions
  setupChatWidget({
    fabId: 'chatbotFab',
    panelId: 'chatbotPanel',
    messagesId: 'widgetMessages',
    inputId: 'widgetInput',
    sendBtnId: 'widgetSendBtn',
    clearBtnId: 'chatbotClearBtn',
    askUrl: config.askUrl,
    clearUrl: config.clearUrl,
    csrfToken: config.csrfToken,
  });
}

function setupChatWidget({ fabId, panelId, messagesId, inputId, sendBtnId, clearBtnId, askUrl, clearUrl, csrfToken }) {
  const fab = document.getElementById(fabId);
  const panel = document.getElementById(panelId);
  const messagesEl = document.getElementById(messagesId);
  const inputEl = document.getElementById(inputId);
  const sendBtn = document.getElementById(sendBtnId);
  const clearBtn = clearBtnId ? document.getElementById(clearBtnId) : null;

  if (!fab || !panel) return;

  let isOpen = false;
  let isTyping = false;

  // Toggle panel
  fab.addEventListener('click', () => {
    isOpen = !isOpen;
    fab.classList.toggle('is-open', isOpen);
    panel.classList.toggle('is-open', isOpen);
    if (isOpen) {
      setTimeout(() => inputEl && inputEl.focus(), 350);
      scrollToBottom(messagesEl);
    }
  });

  // Auto-resize textarea
  if (inputEl) {
    inputEl.addEventListener('input', () => {
      inputEl.style.height = 'auto';
      inputEl.style.height = Math.min(inputEl.scrollHeight, 100) + 'px';
      if (sendBtn) sendBtn.disabled = !inputEl.value.trim();
    });

    inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!sendBtn.disabled && !isTyping) sendMessage();
      }
    });
  }

  if (sendBtn) {
    sendBtn.addEventListener('click', () => {
      if (!isTyping) sendMessage();
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener('click', () => clearConversation());
  }

  async function sendMessage() {
    const message = inputEl.value.trim();
    if (!message || isTyping) return;

    isTyping = true;
    sendBtn.disabled = true;
    inputEl.value = '';
    inputEl.style.height = 'auto';

    // Ajouter le message utilisateur
    appendMessage(messagesEl, 'user', message);

    // Indicateur de frappe
    const typingEl = appendTypingIndicator(messagesEl);

    try {
      const res = await fetch(askUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({ message }),
      });

      const data = await res.json();
      typingEl.remove();

      if (data.answer) {
        appendMessage(messagesEl, 'ai', data.answer);
      } else if (data.error) {
        appendMessage(messagesEl, 'ai', `❌ ${data.error}`);
      }
    } catch (err) {
      typingEl.remove();
      appendMessage(messagesEl, 'ai', '❌ Erreur de connexion. Vérifiez votre réseau.');
    } finally {
      isTyping = false;
      if (inputEl.value.trim()) sendBtn.disabled = false;
    }
  }

  async function clearConversation() {
    if (!clearUrl) return;
    try {
      await fetch(clearUrl, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken },
      });
      // Vider les messages sauf le premier (bienvenue)
      const messages = messagesEl.querySelectorAll('.chat-message');
      messages.forEach((m, i) => { if (i > 0) m.remove(); });
    } catch (e) {
      console.error('Clear failed:', e);
    }
  }
}

/* ══════════════════════════════════════════════════════════════
   PAGE DÉDIÉE
══════════════════════════════════════════════════════════════ */

function initChatbotPage() {
  const config = window.APM_CHATBOT_CONFIG || {};
  if (!config.askUrl) return;

  const messagesEl = document.getElementById('chatMessages');
  const inputEl = document.getElementById('chatInput');
  const sendBtn = document.getElementById('chatSendBtn');
  const clearBtn = document.getElementById('clearHistoryBtn');
  const suggestionsEl = document.getElementById('chatSuggestions');

  if (!messagesEl) return;

  let isTyping = false;

  // Scroll au bas au chargement
  scrollToBottom(messagesEl);

  // Rendre le markdown existant dans l'historique
  messagesEl.querySelectorAll('.markdown-content').forEach(el => {
    el.innerHTML = parseMarkdown(el.textContent || el.innerText);
  });

  // Auto-resize
  if (inputEl) {
    inputEl.addEventListener('input', () => {
      inputEl.style.height = 'auto';
      inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + 'px';
      sendBtn.disabled = !inputEl.value.trim();
    });

    inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!sendBtn.disabled && !isTyping) sendMessage();
      }
    });
  }

  if (sendBtn) {
    sendBtn.addEventListener('click', () => {
      if (!isTyping) sendMessage();
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener('click', async () => {
      if (!confirm('Effacer toute la conversation ?')) return;
      try {
        await fetch(config.clearUrl, {
          method: 'POST',
          headers: { 'X-CSRFToken': config.csrfToken },
        });
        const msgs = messagesEl.querySelectorAll('.chat-message');
        msgs.forEach((m, i) => { if (i > 0) m.remove(); });
      } catch(e) { console.error(e); }
    });
  }

  // Suggestions rapides
  if (suggestionsEl) {
    suggestionsEl.querySelectorAll('.suggestion-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const q = chip.dataset.q;
        if (q && inputEl) {
          inputEl.value = q;
          inputEl.dispatchEvent(new Event('input'));
          suggestionsEl.style.display = 'none';
          sendMessage();
        }
      });
    });
  }

  async function sendMessage() {
    const message = inputEl.value.trim();
    if (!message || isTyping) return;

    isTyping = true;
    sendBtn.disabled = true;
    inputEl.value = '';
    inputEl.style.height = 'auto';

    // Masquer les suggestions après le 1er message
    if (suggestionsEl) suggestionsEl.style.display = 'none';

    appendMessage(messagesEl, 'user', message);
    const typingEl = appendTypingIndicator(messagesEl);
    scrollToBottom(messagesEl);

    try {
      const res = await fetch(config.askUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': config.csrfToken,
        },
        body: JSON.stringify({ message }),
      });

      const data = await res.json();
      typingEl.remove();

      if (data.answer) {
        appendMessage(messagesEl, 'ai', data.answer, true);
      } else if (data.error) {
        appendMessage(messagesEl, 'ai', `❌ ${data.error}`);
      }
    } catch (err) {
      typingEl.remove();
      appendMessage(messagesEl, 'ai', '❌ Erreur de connexion. Vérifiez votre réseau.');
    } finally {
      isTyping = false;
      scrollToBottom(messagesEl);
    }
  }
}

/* ══════════════════════════════════════════════════════════════
   UTILITAIRES PARTAGÉS
══════════════════════════════════════════════════════════════ */

function appendMessage(container, role, content, renderMd = false) {
  const msgDiv = document.createElement('div');
  msgDiv.className = `chat-message chat-message--${role === 'user' ? 'user' : 'ai'}`;

  const bubbleDiv = document.createElement('div');
  bubbleDiv.className = `chat-bubble chat-bubble--${role === 'user' ? 'user' : 'ai'}`;

  if (role === 'ai') {
    const header = document.createElement('div');
    header.className = 'chat-bubble-header';
    header.innerHTML = '<span class="chat-bubble-sender">🤖 Assistant DSI</span>';
    bubbleDiv.appendChild(header);
  }

  const contentDiv = document.createElement('div');
  contentDiv.className = role === 'ai' ? 'chat-bubble-content markdown-content' : 'chat-bubble-content';

  if (role === 'ai' && (renderMd || true)) {
    contentDiv.innerHTML = parseMarkdown(content);
  } else {
    contentDiv.textContent = content;
  }

  bubbleDiv.appendChild(contentDiv);
  msgDiv.appendChild(bubbleDiv);
  container.appendChild(msgDiv);

  scrollToBottom(container);
  return msgDiv;
}

function appendTypingIndicator(container) {
  const msgDiv = document.createElement('div');
  msgDiv.className = 'chat-message chat-message--ai';
  msgDiv.innerHTML = `
    <div class="typing-indicator">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>
  `;
  container.appendChild(msgDiv);
  scrollToBottom(container);
  return msgDiv;
}

function scrollToBottom(el) {
  if (el) {
    requestAnimationFrame(() => {
      el.scrollTop = el.scrollHeight;
    });
  }
}

/**
 * Parser Markdown minimaliste pour les réponses Gemini.
 * Supporte : gras, italique, code inline, blocs code, listes, tableaux, titres.
 */
function parseMarkdown(text) {
  if (!text) return '';

  let html = text
    // Échapper HTML d'abord
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Blocs de code (```...```)
  html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
    return `<pre><code>${code.trim()}</code></pre>`;
  });

  // Code inline (`...`)
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Titres
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h2>$1</h2>');

  // Gras + italique
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // Tableaux markdown (simple)
  html = html.replace(/(?:^\|.+\|$\n?)+/gm, (tableBlock) => {
    const rows = tableBlock.trim().split('\n');
    if (rows.length < 2) return tableBlock;
    const header = rows[0];
    const body = rows.slice(2); // sauter la ligne de séparation
    const thCells = header.split('|').filter(c => c.trim()).map(c => `<th>${c.trim()}</th>`).join('');
    const bodyRows = body.map(row => {
      const cells = row.split('|').filter(c => c.trim()).map(c => `<td>${c.trim()}</td>`).join('');
      return `<tr>${cells}</tr>`;
    }).join('');
    return `<table><thead><tr>${thCells}</tr></thead><tbody>${bodyRows}</tbody></table>`;
  });

  // Listes non ordonnées
  html = html.replace(/^[\s]*[-*•] (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>[\s\S]*?<\/li>)/g, (block) => `<ul>${block}</ul>`);
  // Nettoyer les ul imbriqués
  html = html.replace(/<\/ul>\s*<ul>/g, '');

  // Listes ordonnées
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

  // Sauts de ligne → <br> (hors blocs pre)
  html = html.replace(/\n(?!<[\/]?(pre|ul|ol|li|h[123]|table|thead|tbody|tr|th|td))/g, '<br>');

  // Nettoyer les <br> excédentaires
  html = html.replace(/(<br>){3,}/g, '<br><br>');
  html = html.replace(/^(<br>)+|(<br>)+$/g, '');

  return html;
}

/* ══════════════════════════════════════════════════════════════
   AUTO-INITIALISATION
══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
  const config = window.APM_CHATBOT_CONFIG || {};

  if (config.mode === 'page') {
    // La page dédiée s'initialise elle-même via son propre appel
    return;
  }

  // Widget flottant : activer sur toutes les pages
  if (config.askUrl) {
    initChatbotWidget();
  }
});
