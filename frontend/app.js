/**
 * SmartAgent Frontend Application Logic
 * Manages Chat State, Tool Visualizations, API Calls, LocalStorage, and Mode Toggling.
 */

(() => {
  // DOM Elements
  const chatContainer = document.getElementById('chatContainer');
  const messagesList = document.getElementById('messagesList');
  const welcomeScreen = document.getElementById('welcomeScreen');
  const thinkingState = document.getElementById('thinkingState');
  const thinkingLabel = document.getElementById('thinkingLabel');
  const messageInput = document.getElementById('messageInput');
  const chatForm = document.getElementById('chatForm');
  const sendBtn = document.getElementById('sendBtn');
  const newChatBtn = document.getElementById('newChatBtn');
  const resetChatBtn = document.getElementById('resetChatBtn');
  const clearHistoryBtn = document.getElementById('clearHistoryBtn');
  const chatHistoryList = document.getElementById('chatHistoryList');
  const sidebar = document.getElementById('sidebar');
  const sidebarBackdrop = document.getElementById('sidebarBackdrop');
  const openSidebarBtn = document.getElementById('openSidebarBtn');
  const closeSidebarBtn = document.getElementById('closeSidebarBtn');
  const statusPill = document.getElementById('statusPill');
  const statusText = document.getElementById('statusText');
  const modeTitle = document.getElementById('modeTitle');
  const modeSubtitle = document.getElementById('modeSubtitle');
  const modeSwitchBtn = document.getElementById('modeSwitchBtn');
  const runDemoBtn = document.getElementById('runDemoBtn');

  // Application State
  const STORAGE_KEY = 'smartagent_conversations_v1';
  let conversations = [];
  let currentChatId = null;
  let isThinking = false;
  let mockMode = false;
  let demoRunning = false;

  // Tool Icons & Metadata Helper
  const TOOL_METADATA = {
    calculate: {
      name: 'Calculator',
      icon: '🧮',
      verb: 'Calculating',
      done: 'Calculation completed',
      formatArg: (args) => args.expression || 'Mathematical expression'
    },
    get_weather: {
      name: 'Weather Lookup',
      icon: '🌤️',
      verb: 'Fetching weather for',
      done: 'Weather information retrieved',
      formatArg: (args) => args.location || 'Location'
    },
    text_operations: {
      name: 'Text Utility',
      icon: '📝',
      verb: 'Processing text',
      done: 'Text transformation completed',
      formatArg: (args) => args.operation ? `${args.operation} on "${args.text}"` : (args.text || 'Text')
    },
    convert_currency: {
      name: 'Currency Converter',
      icon: '💱',
      verb: 'Converting',
      done: 'Currency conversion completed',
      formatArg: (args) => `${args.amount || 0} ${args.from_currency || 'USD'} → ${args.to_currency || 'INR'}`
    }
  };

  /* ==========================================================================
     Initialization & Local Storage Management
     ========================================================================== */

  function initApp() {
    loadConversations();
    setupEventListeners();
    fetchServerStatus();

    // Start with a new chat or load latest
    if (conversations.length > 0) {
      loadChat(conversations[0].id);
    } else {
      createNewChat();
    }
  }

  function loadConversations() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      conversations = stored ? JSON.parse(stored) : [];
    } catch (e) {
      console.error('Error loading conversations from localStorage:', e);
      conversations = [];
    }
    renderHistorySidebar();
  }

  function saveConversations() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
    } catch (e) {
      console.error('Error saving conversations:', e);
    }
    renderHistorySidebar();
  }

  function getCurrentChat() {
    return conversations.find(c => c.id === currentChatId);
  }

  function createNewChat() {
    currentChatId = 'chat_' + Date.now();
    const newChat = {
      id: currentChatId,
      title: 'New Conversation',
      createdAt: new Date().toISOString(),
      messages: []
    };
    conversations.unshift(newChat);
    saveConversations();
    renderChatView();
    if (messageInput) {
      messageInput.focus();
    }
  }

  function loadChat(chatId) {
    currentChatId = chatId;
    renderChatView();
    renderHistorySidebar();
    closeMobileSidebar();
  }

  function deleteChat(chatId, event) {
    if (event) event.stopPropagation();
    conversations = conversations.filter(c => c.id !== chatId);
    saveConversations();
    if (currentChatId === chatId) {
      if (conversations.length > 0) {
        loadChat(conversations[0].id);
      } else {
        createNewChat();
      }
    }
  }

  function clearAllHistory() {
    if (confirm('Clear all conversation history?')) {
      conversations = [];
      saveConversations();
      createNewChat();
    }
  }

  /* ==========================================================================
     API Server Communication
     ========================================================================== */

  async function fetchServerStatus() {
    try {
      const res = await fetch('/api/status');
      if (res.ok) {
        const data = await res.json();
        mockMode = !!data.mock_mode;
        updateModeUI(mockMode, data.model);
      }
    } catch (err) {
      console.warn('Unable to reach /api/status:', err);
    }
  }

  async function toggleServerMode() {
    mockMode = !mockMode;
    try {
      const res = await fetch('/api/mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mock_mode: mockMode })
      });
      if (res.ok) {
        const data = await res.json();
        mockMode = data.mock_mode;
      }
    } catch (e) {
      console.warn('Mode switch request failed:', e);
    }
    updateModeUI(mockMode);
  }

  function updateModeUI(isMock, modelName) {
    if (isMock) {
      modeSwitchBtn.classList.add('mock-active');
      modeTitle.textContent = 'Local Dev Mode';
      modeSubtitle.textContent = 'Zero API quota used (Fast)';
      statusPill.classList.add('mock-mode');
      statusText.textContent = 'Dev Mode (0 Quota)';
    } else {
      modeSwitchBtn.classList.remove('mock-active');
      modeTitle.textContent = 'Live Gemini LLM';
      modeSubtitle.textContent = modelName ? `Model: ${modelName}` : 'Tool execution pipeline active';
      statusPill.classList.remove('mock-mode');
      statusText.textContent = 'Online';
    }
  }

  /* ==========================================================================
     Chat View Rendering
     ========================================================================== */

  function renderChatView() {
    const chat = getCurrentChat();
    messagesList.innerHTML = '';

    if (!chat || !chat.messages || chat.messages.length === 0) {
      welcomeScreen.style.display = 'flex';
      messagesList.style.display = 'none';
    } else {
      welcomeScreen.style.display = 'none';
      messagesList.style.display = 'flex';
      chat.messages.forEach(msg => {
        const msgNode = createMessageElement(msg);
        messagesList.appendChild(msgNode);
      });
    }
    scrollToBottom();
  }

  function renderHistorySidebar() {
    chatHistoryList.innerHTML = '';
    if (conversations.length === 0) {
      chatHistoryList.innerHTML = '<div class="history-empty">No past conversations</div>';
      return;
    }

    conversations.forEach(chat => {
      const item = document.createElement('div');
      item.className = `history-item ${chat.id === currentChatId ? 'active' : ''}`;
      item.onclick = () => loadChat(chat.id);

      const titleSpan = document.createElement('span');
      titleSpan.className = 'history-title';
      titleSpan.textContent = chat.title || 'Conversation';

      const deleteBtn = document.createElement('button');
      deleteBtn.className = 'btn-delete-history';
      deleteBtn.title = 'Delete chat';
      deleteBtn.innerHTML = '&times;';
      deleteBtn.onclick = (e) => deleteChat(chat.id, e);

      item.appendChild(titleSpan);
      item.appendChild(deleteBtn);
      chatHistoryList.appendChild(item);
    });
  }

  function formatMarkdown(text) {
    if (!text) return '';
    let escaped = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Code blocks ```code```
    escaped = escaped.replace(/```([\s\S]*?)```/g, (match, p1) => {
      return `<pre><code>${p1.trim()}</code></pre>`;
    });

    // Inline code `code`
    escaped = escaped.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Bold **text**
    escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // Bullet points (- or *)
    const lines = escaped.split('\n');
    let inList = false;
    let formattedLines = [];

    for (let line of lines) {
      const bulletMatch = line.match(/^(\s*)[-*•]\s+(.*)$/);
      if (bulletMatch) {
        if (!inList) {
          formattedLines.push('<ul>');
          inList = true;
        }
        formattedLines.push(`<li>${bulletMatch[2]}</li>`);
      } else {
        if (inList) {
          formattedLines.push('</ul>');
          inList = false;
        }
        if (line.trim() === '') {
          formattedLines.push('<br>');
        } else {
          formattedLines.push(`<p>${line}</p>`);
        }
      }
    }
    if (inList) formattedLines.push('</ul>');

    return formattedLines.join('');
  }

  function createToolCardElement(toolName, toolArgs, toolResult, elapsedMs) {
    const meta = TOOL_METADATA[toolName] || {
      name: toolName || 'Tool Execution',
      icon: '⚙️',
      verb: 'Executing',
      done: 'Completed',
      formatArg: (a) => JSON.stringify(a)
    };

    const card = document.createElement('div');
    card.className = 'tool-card';

    const argText = meta.formatArg(toolArgs || {});
    const timeText = elapsedMs ? ` (${elapsedMs}ms)` : '';

    card.innerHTML = `
      <div class="tool-card-header">
        <div class="tool-card-identity">
          <span class="tool-card-icon">${meta.icon}</span>
          <span class="tool-card-name">${meta.name}</span>
        </div>
        <div class="tool-card-status">
          <span>✓</span>
          <span>${meta.done}${timeText}</span>
        </div>
      </div>
      <div class="tool-card-body">
        <div class="tool-card-action">${meta.verb}: <strong>${escapeHtml(argText)}</strong></div>
        <button type="button" class="tool-card-details-toggle">▸ View raw execution payload</button>
        <div class="tool-card-raw" style="display: none;">
          <pre>${escapeHtml(JSON.stringify({ tool: toolName, arguments: toolArgs, result: toolResult }, null, 2))}</pre>
        </div>
      </div>
    `;

    const toggleBtn = card.querySelector('.tool-card-details-toggle');
    const rawBox = card.querySelector('.tool-card-raw');
    toggleBtn.addEventListener('click', () => {
      const isHidden = rawBox.style.display === 'none';
      rawBox.style.display = isHidden ? 'block' : 'none';
      toggleBtn.textContent = isHidden ? '▾ Hide execution payload' : '▸ View raw execution payload';
    });

    return card;
  }

  function createMessageElement(msg) {
    const row = document.createElement('div');
    row.className = `message-row ${msg.role === 'user' ? 'user-row' : 'agent-row'}`;

    if (msg.role === 'user') {
      const bubble = document.createElement('div');
      bubble.className = 'user-bubble';
      bubble.textContent = msg.content;
      row.appendChild(bubble);
    } else {
      // Agent Message
      const avatarWrap = document.createElement('div');
      avatarWrap.className = 'agent-avatar-wrap';
      avatarWrap.innerHTML = '<span class="agent-avatar-icon">✦</span>';

      const contentWrap = document.createElement('div');
      contentWrap.className = 'agent-content-wrap';

      // If a tool was invoked, render Tool Execution Card first
      if (msg.tool_called) {
        const toolCard = createToolCardElement(
          msg.tool_called,
          msg.tool_args,
          msg.tool_result,
          msg.elapsed_ms
        );
        contentWrap.appendChild(toolCard);
      }

      // Render AI synthesized response
      const bubble = document.createElement('div');
      bubble.className = 'agent-bubble';
      bubble.innerHTML = formatMarkdown(msg.content);
      contentWrap.appendChild(bubble);

      // Meta bar with copy action
      const metaBar = document.createElement('div');
      metaBar.className = 'agent-meta-bar';
      metaBar.innerHTML = `
        <button class="btn-copy" title="Copy response">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
          <span>Copy</span>
        </button>
      `;
      const copyBtn = metaBar.querySelector('.btn-copy');
      copyBtn.onclick = () => {
        navigator.clipboard.writeText(msg.content).then(() => {
          copyBtn.querySelector('span').textContent = 'Copied!';
          setTimeout(() => { copyBtn.querySelector('span').textContent = 'Copy'; }, 2000);
        });
      };
      contentWrap.appendChild(metaBar);

      row.appendChild(avatarWrap);
      row.appendChild(contentWrap);
    }

    return row;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function scrollToBottom() {
    setTimeout(() => {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }, 50);
  }

  /* ==========================================================================
     Send Message Handling & AI Tool Dispatch
     ========================================================================== */

  async function handleSendMessage(promptText) {
    const text = (promptText || messageInput.value || '').trim();
    if (!text || isThinking) return;

    messageInput.value = '';
    autoResizeTextarea();

    let chat = getCurrentChat();
    if (!chat) {
      createNewChat();
      chat = getCurrentChat();
    }

    // Auto-title conversation on first message
    if (chat.messages.length === 0) {
      chat.title = text.length > 28 ? text.substring(0, 25) + '...' : text;
      saveConversations();
    }

    // 1. Add User message to state & UI
    const userMsg = { role: 'user', content: text, timestamp: new Date().toISOString() };
    chat.messages.push(userMsg);
    saveConversations();
    renderChatView();

    // 2. Show thinking state
    isThinking = true;
    sendBtn.disabled = true;
    thinkingState.style.display = 'flex';
    thinkingLabel.textContent = mockMode ? 'SmartAgent is analyzing query (Dev Mode)...' : 'SmartAgent is determining tool...';
    scrollToBottom();

    // 3. Send to API Server
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          mock_mode: mockMode
        })
      });

      const data = await response.json();

      if (response.ok && data.success !== false) {
        const agentMsg = {
          role: 'agent',
          content: data.response || 'I completed your request.',
          tool_called: data.tool_called,
          tool_args: data.tool_args,
          tool_result: data.tool_result,
          elapsed_ms: data.elapsed_ms,
          timestamp: new Date().toISOString()
        };
        chat.messages.push(agentMsg);
        saveConversations();
        renderChatView();
      } else {
        const errorMsg = {
          role: 'agent',
          content: `⚠️ ${data.error || 'Something went wrong while processing your request. Please try again.'}`,
          timestamp: new Date().toISOString()
        };
        chat.messages.push(errorMsg);
        saveConversations();
        renderChatView();
      }
    } catch (err) {
      console.error('API call error:', err);
      const errorMsg = {
        role: 'agent',
        content: '⚠️ Unable to connect to the backend server. Please make sure the server is running.',
        timestamp: new Date().toISOString()
      };
      chat.messages.push(errorMsg);
      saveConversations();
      renderChatView();
    } finally {
      isThinking = false;
      sendBtn.disabled = false;
      thinkingState.style.display = 'none';
      scrollToBottom();
      messageInput.focus();
    }
  }

  /* ==========================================================================
     Automated Demo Runner
     ========================================================================== */

  async function runDemoShowcase() {
    if (demoRunning || isThinking) return;
    demoRunning = true;
    runDemoBtn.disabled = true;
    runDemoBtn.innerHTML = '<span>⏳ Running Demo...</span>';

    try {
      const res = await fetch('/api/demo');
      const data = await res.json();
      const prompts = data.prompts || [];

      createNewChat();
      const chat = getCurrentChat();
      chat.title = '✨ Automated 2-Min Demo';
      saveConversations();

      for (let i = 0; i < prompts.length; i++) {
        const p = prompts[i];
        await handleSendMessage(p.prompt);
        // Wait 3.5 seconds between demo queries
        if (i < prompts.length - 1) {
          await new Promise(r => setTimeout(r, 3500));
        }
      }
    } catch (err) {
      console.error('Demo error:', err);
    } finally {
      demoRunning = false;
      runDemoBtn.disabled = false;
      runDemoBtn.innerHTML = '<span>✨ Run Demo</span>';
    }
  }

  /* ==========================================================================
     Event Listeners
     ========================================================================== */

  function setupEventListeners() {
    // Chat Form Submit
    chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      handleSendMessage();
    });

    // Keydown in message textarea (Enter to send, Shift+Enter for newline)
    messageInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
      }
    });

    // Auto resize textarea
    messageInput.addEventListener('input', autoResizeTextarea);

    // New Chat Button
    newChatBtn.addEventListener('click', createNewChat);

    // Reset Chat Button in Header
    resetChatBtn.addEventListener('click', () => {
      if (confirm('Clear current conversation messages?')) {
        const chat = getCurrentChat();
        if (chat) {
          chat.messages = [];
          saveConversations();
          renderChatView();
        }
      }
    });

    // Clear History Button
    clearHistoryBtn.addEventListener('click', clearAllHistory);

    // Mode Switch Button
    modeSwitchBtn.addEventListener('click', toggleServerMode);

    // Demo Button
    runDemoBtn.addEventListener('click', runDemoShowcase);

    // Mobile Sidebar Drawer
    openSidebarBtn.addEventListener('click', openMobileSidebar);
    closeSidebarBtn.addEventListener('click', closeMobileSidebar);
    sidebarBackdrop.addEventListener('click', closeMobileSidebar);

    // Quick Prompt Chips & Suggestion Cards
    document.addEventListener('click', (e) => {
      const card = e.target.closest('.suggestion-card, .quick-chip, .tool-item');
      if (card && card.dataset.prompt) {
        const prompt = card.dataset.prompt;
        handleSendMessage(prompt);
      }
    });
  }

  function autoResizeTextarea() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 160) + 'px';
  }

  function openMobileSidebar() {
    sidebar.classList.add('open');
    sidebarBackdrop.classList.add('open');
  }

  function closeMobileSidebar() {
    sidebar.classList.remove('open');
    sidebarBackdrop.classList.remove('open');
  }

  // Start Application
  window.addEventListener('DOMContentLoaded', initApp);
})();
