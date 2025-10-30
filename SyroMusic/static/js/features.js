/* ========================================
   SyroMusic Advanced Features
   - Search History
   - Mini Player
   - Playlist Collaboration
   - Social Features
   - Offline Mode
   - Track Lyrics
   - Audio Visualization
   - Playback Analytics
   - Smart Queue Management
   ======================================== */

const CSRF_TOKEN = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

/* ========== 1. SEARCH HISTORY ========== */
const SearchHistory = {
  save: async function(query, searchType = 'all') {
    try {
      const response = await fetch('/music/api/search-history/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': CSRF_TOKEN,
        },
        body: JSON.stringify({
          query: query,
          search_type: searchType,
        }),
      });
      return await response.json();
    } catch (error) {
      console.error('Error saving search history:', error);
    }
  },

  get: async function(limit = 20) {
    try {
      const response = await fetch(`/music/api/search-history/?limit=${limit}`, {
        headers: {
          'X-CSRFToken': CSRF_TOKEN,
        },
      });
      const data = await response.json();
      return data.data || [];
    } catch (error) {
      console.error('Error fetching search history:', error);
      return [];
    }
  },

  clear: async function() {
    try {
      const response = await fetch('/music/api/search-history/clear/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': CSRF_TOKEN,
        },
      });
      return await response.json();
    } catch (error) {
      console.error('Error clearing search history:', error);
    }
  },

  displayHistory: async function(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const history = await this.get();
    if (history.length === 0) {
      container.innerHTML = '<p class="text-gray-500">No search history</p>';
      return;
    }

    container.innerHTML = history.map(item => `
      <div class="p-3 hover:bg-gray-800 rounded cursor-pointer search-history-item" data-query="${item.query}">
        <span class="text-sm">${item.query}</span>
        <span class="text-xs text-gray-500 ml-2">${item.search_type}</span>
      </div>
    `).join('');

    container.querySelectorAll('.search-history-item').forEach(item => {
      item.addEventListener('click', () => {
        document.querySelector('[name="q"]').value = item.dataset.query;
        document.querySelector('form').submit();
      });
    });
  },
};

/* ========== 2. MINI PLAYER WIDGET ========== */
const MiniPlayer = {
  isMinimized: false,
  isVisible: true,

  init: function() {
    this.createWidget();
    this.attachEventListeners();
    this.loadState();
  },

  createWidget: function() {
    const miniPlayerHTML = `
      <div id="mini-player" class="fixed bottom-4 right-4 w-80 bg-gray-900 rounded-lg shadow-2xl border border-gray-700 z-50 transition-all duration-300">
        <div class="p-4">
          <div class="flex justify-between items-center mb-3">
            <h3 class="text-sm font-bold text-white">Now Playing</h3>
            <div class="flex gap-2">
              <button id="mini-toggle" class="text-gray-400 hover:text-white text-xs">Minimize</button>
              <button id="mini-close" class="text-gray-400 hover:text-white">×</button>
            </div>
          </div>

          <div id="mini-content" class="space-y-3">
            <img id="mini-album-art" src="" alt="" class="w-full h-40 rounded-lg object-cover">

            <div>
              <p id="mini-track-name" class="font-semibold text-white truncate">No track playing</p>
              <p id="mini-artist-name" class="text-sm text-gray-400 truncate">-</p>
            </div>

            <div class="flex justify-around">
              <button id="mini-play" class="text-white hover:text-green-400" title="Play/Pause">
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z"></path></svg>
              </button>
              <button id="mini-next" class="text-white hover:text-green-400" title="Next">
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M4.555 7.168A1 1 0 003 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"></path><path d="M12.555 7.168A1 1 0 0011 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"></path></svg>
              </button>
              <button id="mini-like" class="text-white hover:text-red-400" title="Like">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path></svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', miniPlayerHTML);
  },

  attachEventListeners: function() {
    document.getElementById('mini-toggle').addEventListener('click', () => this.toggle());
    document.getElementById('mini-close').addEventListener('click', () => this.hide());
    document.getElementById('mini-play').addEventListener('click', () => this.playPause());
    document.getElementById('mini-next').addEventListener('click', () => this.nextTrack());
    document.getElementById('mini-like').addEventListener('click', () => this.likeTrack());
  },

  toggle: function() {
    this.isMinimized = !this.isMinimized;
    const content = document.getElementById('mini-content');
    const button = document.getElementById('mini-toggle');

    if (this.isMinimized) {
      content.style.display = 'none';
      button.textContent = 'Expand';
    } else {
      content.style.display = 'block';
      button.textContent = 'Minimize';
    }

    localStorage.setItem('miniPlayerMinimized', this.isMinimized);
  },

  hide: function() {
    document.getElementById('mini-player').style.display = 'none';
    this.isVisible = false;
    localStorage.setItem('miniPlayerVisible', false);
  },

  show: function() {
    document.getElementById('mini-player').style.display = 'block';
    this.isVisible = true;
    localStorage.setItem('miniPlayerVisible', true);
  },

  updateTrack: function(trackData) {
    document.getElementById('mini-track-name').textContent = trackData.name || 'Unknown';
    document.getElementById('mini-artist-name').textContent = trackData.artists?.[0]?.name || 'Unknown Artist';
    if (trackData.album?.images?.[0]?.url) {
      document.getElementById('mini-album-art').src = trackData.album.images[0].url;
    }
  },

  playPause: async function() {
    const response = await fetch('/music/api/playback/pause/', {
      method: 'POST',
      headers: { 'X-CSRFToken': CSRF_TOKEN },
    });
    return await response.json();
  },

  nextTrack: async function() {
    const response = await fetch('/music/api/playback/next/', {
      method: 'POST',
      headers: { 'X-CSRFToken': CSRF_TOKEN },
    });
    return await response.json();
  },

  likeTrack: function() {
    console.log('Like track functionality');
  },

  loadState: function() {
    const minimized = localStorage.getItem('miniPlayerMinimized') === 'true';
    const visible = localStorage.getItem('miniPlayerVisible') !== 'false';

    if (!visible) this.hide();
    if (minimized) this.toggle();
  },
};

/* ========== 3. PLAYLIST COLLABORATION ========== */
const PlaylistCollaboration = {
  addCollaborator: async function(playlistId, username, permissionLevel = 'view') {
    try {
      const response = await fetch('/music/api/collaborator/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': CSRF_TOKEN,
        },
        body: JSON.stringify({
          playlist_id: playlistId,
          username: username,
          permission_level: permissionLevel,
        }),
      });
      return await response.json();
    } catch (error) {
      console.error('Error adding collaborator:', error);
    }
  },

  sharePlaylist: async function(playlistId, username, message = '') {
    try {
      const response = await fetch('/music/api/share-playlist/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': CSRF_TOKEN,
        },
        body: JSON.stringify({
          playlist_id: playlistId,
          username: username,
          message: message,
        }),
      });
      return await response.json();
    } catch (error) {
      console.error('Error sharing playlist:', error);
    }
  },
};

/* ========== 4. SOCIAL FEATURES ========== */
const SocialFeatures = {
  userProfile: {
    get: async function() {
      try {
        const response = await fetch('/music/api/profile/', {
          headers: { 'X-CSRFToken': CSRF_TOKEN },
        });
        const data = await response.json();
        return data.data;
      } catch (error) {
        console.error('Error fetching profile:', error);
      }
    },

    update: async function(profileData) {
      try {
        const response = await fetch('/music/api/profile/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF_TOKEN,
          },
          body: JSON.stringify(profileData),
        });
        return await response.json();
      } catch (error) {
        console.error('Error updating profile:', error);
      }
    },
  },

  followUser: async function(username) {
    try {
      const response = await fetch('/music/api/follow/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': CSRF_TOKEN,
        },
        body: JSON.stringify({ username: username }),
      });
      return await response.json();
    } catch (error) {
      console.error('Error following user:', error);
    }
  },

  unfollowUser: async function(username) {
    try {
      const response = await fetch('/music/api/unfollow/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': CSRF_TOKEN,
        },
        body: JSON.stringify({ username: username }),
      });
      return await response.json();
    } catch (error) {
      console.error('Error unfollowing user:', error);
    }
  },
};

/* ========== 5. OFFLINE MODE ========== */
const OfflineMode = {
  isOnline: navigator.onLine,

  init: function() {
    window.addEventListener('online', () => this.goOnline());
    window.addEventListener('offline', () => this.goOffline());
    this.registerServiceWorker();
  },

  registerServiceWorker: function() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/static/js/sw.js').catch(err => {
        console.log('Service Worker registration failed:', err);
      });
    }
  },

  goOnline: function() {
    this.isOnline = true;
    console.log('App is now online');
    document.body.classList.remove('offline-mode');
    this.syncData();
  },

  goOffline: function() {
    this.isOnline = false;
    console.log('App is now offline');
    document.body.classList.add('offline-mode');
  },

  syncData: function() {
    console.log('Syncing data...');
  },

  cacheData: function(key, data) {
    localStorage.setItem(`offline_${key}`, JSON.stringify(data));
  },

  getCachedData: function(key) {
    const data = localStorage.getItem(`offline_${key}`);
    return data ? JSON.parse(data) : null;
  },
};

/* ========== 6. TRACK LYRICS ========== */
const TrackLyrics = {
  get: async function(spotifyTrackId) {
    try {
      const response = await fetch(`/music/api/lyrics/?spotify_track_id=${spotifyTrackId}`, {
        headers: { 'X-CSRFToken': CSRF_TOKEN },
      });
      const data = await response.json();
      return data.status === 'success' ? data.data : null;
    } catch (error) {
      console.error('Error fetching lyrics:', error);
      return null;
    }
  },

  display: function(lyricsData, containerId) {
    const container = document.getElementById(containerId);
    if (!container || !lyricsData) return;

    const lyricsLines = lyricsData.lyrics.split('\n');
    const html = `
      <div class="lyrics-container p-6 text-white text-center">
        <p class="text-xs text-gray-500 mb-4">Lyrics from ${lyricsData.source}</p>
        ${lyricsLines.map(line => `<p class="mb-2 text-lg leading-relaxed">${line}</p>`).join('')}
      </div>
    `;

    container.innerHTML = html;
  },

  showModal: async function(trackName, spotifyTrackId) {
    const lyrics = await this.get(spotifyTrackId);

    if (!lyrics) {
      alert('Lyrics not available for this track');
      return;
    }

    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4';
    modal.innerHTML = `
      <div class="bg-gray-900 rounded-lg max-w-2xl max-h-96 overflow-y-auto w-full">
        <div class="p-6">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-2xl font-bold text-white">${trackName}</h2>
            <button onclick="this.closest('div.fixed').remove()" class="text-gray-400 hover:text-white text-2xl">×</button>
          </div>
          <div class="text-white whitespace-pre-wrap text-sm">
            ${lyrics.lyrics}
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
  },
};

/* ========== 7. AUDIO VISUALIZATION ========== */
const AudioVisualizer = {
  styles: ['bars', 'waveform', 'circles', 'spectrum'],
  currentStyle: 'bars',
  canvas: null,
  ctx: null,
  dataArray: null,
  analyser: null,

  init: function(canvasId, audioContext, analyser) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d');
    this.analyser = analyser;
    this.dataArray = new Uint8Array(analyser.frequencyBinCount);
    this.animate();
  },

  animate: function() {
    requestAnimationFrame(() => this.animate());

    if (!this.analyser) return;

    this.analyser.getByteFrequencyData(this.dataArray);

    switch (this.currentStyle) {
      case 'bars':
        this.drawBars();
        break;
      case 'waveform':
        this.drawWaveform();
        break;
      case 'circles':
        this.drawCircles();
        break;
      case 'spectrum':
        this.drawSpectrum();
        break;
    }
  },

  drawBars: function() {
    const width = this.canvas.width;
    const height = this.canvas.height;

    this.ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
    this.ctx.fillRect(0, 0, width, height);

    const barWidth = (width / this.dataArray.length) * 2.5;
    let x = 0;

    for (let i = 0; i < this.dataArray.length; i++) {
      const barHeight = (this.dataArray[i] / 255) * height;
      const hue = (i / this.dataArray.length) * 360;

      this.ctx.fillStyle = `hsl(${hue}, 100%, 50%)`;
      this.ctx.fillRect(x, height - barHeight, barWidth, barHeight);

      x += barWidth + 1;
    }
  },

  drawWaveform: function() {
    const width = this.canvas.width;
    const height = this.canvas.height;

    this.ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
    this.ctx.fillRect(0, 0, width, height);

    this.ctx.strokeStyle = '#00ff00';
    this.ctx.lineWidth = 2;
    this.ctx.beginPath();

    const sliceWidth = width / this.dataArray.length;
    let x = 0;

    for (let i = 0; i < this.dataArray.length; i++) {
      const v = this.dataArray[i] / 128;
      const y = (v * height) / 2;

      if (i === 0) {
        this.ctx.moveTo(x, y);
      } else {
        this.ctx.lineTo(x, y);
      }

      x += sliceWidth;
    }

    this.ctx.stroke();
  },

  drawCircles: function() {
    const width = this.canvas.width;
    const height = this.canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;

    this.ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
    this.ctx.fillRect(0, 0, width, height);

    const dataSum = this.dataArray.reduce((a, b) => a + b, 0);
    const avgValue = dataSum / this.dataArray.length;
    const radius = (avgValue / 255) * 100 + 50;

    this.ctx.strokeStyle = `hsl(${(avgValue / 255) * 360}, 100%, 50%)`;
    this.ctx.lineWidth = 3;
    this.ctx.beginPath();
    this.ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
    this.ctx.stroke();
  },

  drawSpectrum: function() {
    const width = this.canvas.width;
    const height = this.canvas.height;

    const gradient = this.ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, '#ff0000');
    gradient.addColorStop(0.5, '#00ff00');
    gradient.addColorStop(1, '#0000ff');

    this.ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
    this.ctx.fillRect(0, 0, width, height);

    this.ctx.fillStyle = gradient;

    const barWidth = width / this.dataArray.length;
    for (let i = 0; i < this.dataArray.length; i++) {
      const barHeight = (this.dataArray[i] / 255) * height;
      this.ctx.fillRect(i * barWidth, height - barHeight, barWidth, barHeight);
    }
  },

  setStyle: function(style) {
    if (this.styles.includes(style)) {
      this.currentStyle = style;
      localStorage.setItem('visualizerStyle', style);
    }
  },

  loadSavedStyle: function() {
    const saved = localStorage.getItem('visualizerStyle');
    if (saved) this.currentStyle = saved;
  },
};

/* ========== 8. PLAYBACK ANALYTICS ========== */
const PlaybackAnalytics = {
  get: async function() {
    try {
      const response = await fetch('/music/api/analytics/', {
        headers: { 'X-CSRFToken': CSRF_TOKEN },
      });
      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  },

  displayDashboard: async function(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const analytics = await this.get();
    if (!analytics) {
      container.innerHTML = '<p class="text-gray-500">No analytics data</p>';
      return;
    }

    const daysOfWeek = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const hours = Array.from({length: 24}, (_, i) => `${i}:00`);

    const html = `
      <div class="analytics-dashboard p-6 space-y-6">
        <div class="grid grid-cols-2 gap-4">
          <div class="bg-gray-800 p-4 rounded-lg">
            <p class="text-gray-400 text-sm">Listening Streak</p>
            <p class="text-3xl font-bold text-green-400">${analytics.listening_streak}</p>
            <p class="text-xs text-gray-500">days</p>
          </div>

          <div class="bg-gray-800 p-4 rounded-lg">
            <p class="text-gray-400 text-sm">Total Listening</p>
            <p class="text-3xl font-bold text-blue-400">${Math.floor(analytics.total_listening_minutes / 60)}</p>
            <p class="text-xs text-gray-500">hours</p>
          </div>

          <div class="bg-gray-800 p-4 rounded-lg">
            <p class="text-gray-400 text-sm">Unique Artists</p>
            <p class="text-3xl font-bold text-purple-400">${analytics.unique_artists_heard}</p>
          </div>

          <div class="bg-gray-800 p-4 rounded-lg">
            <p class="text-gray-400 text-sm">Unique Tracks</p>
            <p class="text-3xl font-bold text-pink-400">${analytics.unique_tracks_heard}</p>
          </div>
        </div>

        <div class="bg-gray-800 p-4 rounded-lg">
          <p class="text-gray-400 text-sm mb-2">Most Active</p>
          <p class="text-xl text-white">${hours[analytics.most_active_hour]} on ${daysOfWeek[analytics.most_active_day_of_week]}</p>
        </div>
      </div>
    `;

    container.innerHTML = html;
  },
};

/* ========== 9. SMART QUEUE MANAGEMENT ========== */
const SmartQueue = {
  queueItems: [],
  draggedItem: null,

  get: async function() {
    try {
      const response = await fetch('/music/api/queue/reorder/', {
        headers: { 'X-CSRFToken': CSRF_TOKEN },
      });
      const data = await response.json();
      this.queueItems = data.data || [];
      return this.queueItems;
    } catch (error) {
      console.error('Error fetching queue:', error);
      return [];
    }
  },

  updatePositions: async function(itemIds) {
    try {
      const response = await fetch('/music/api/queue/reorder/update/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': CSRF_TOKEN,
        },
        body: JSON.stringify({ items: itemIds }),
      });
      return await response.json();
    } catch (error) {
      console.error('Error updating queue:', error);
    }
  },

  renderQueue: async function(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const items = await this.get();

    const html = `
      <div id="queue-list" class="space-y-2">
        ${items.map((item, index) => `
          <div class="queue-item p-3 bg-gray-800 rounded hover:bg-gray-700 cursor-move flex justify-between items-center"
               draggable="true" data-item-id="${item.id}" data-position="${index}">
            <div class="flex-1">
              <p class="font-semibold text-white truncate">${item.track_data?.name || 'Unknown'}</p>
              <p class="text-xs text-gray-400 truncate">${item.track_data?.artists?.[0]?.name || 'Unknown Artist'}</p>
            </div>
            <span class="text-xs text-gray-500 ml-2">#${index + 1}</span>
          </div>
        `).join('')}
      </div>
    `;

    container.innerHTML = html;
    this.attachDragListeners();
  },

  attachDragListeners: function() {
    const items = document.querySelectorAll('.queue-item');

    items.forEach(item => {
      item.addEventListener('dragstart', (e) => {
        this.draggedItem = item;
        item.style.opacity = '0.5';
      });

      item.addEventListener('dragend', () => {
        item.style.opacity = '1';
        this.draggedItem = null;
        this.updateOrderInDB();
      });

      item.addEventListener('dragover', (e) => {
        e.preventDefault();
        if (this.draggedItem && this.draggedItem !== item) {
          item.parentNode.insertBefore(this.draggedItem, item);
        }
      });
    });
  },

  updateOrderInDB: async function() {
    const items = document.querySelectorAll('.queue-item');
    const itemIds = Array.from(items).map(item => item.dataset.itemId);
    await this.updatePositions(itemIds);
  },
};

/* ========== INITIALIZATION ========== */
document.addEventListener('DOMContentLoaded', function() {
  MiniPlayer.init();
  OfflineMode.init();
  AudioVisualizer.loadSavedStyle();
});

/* Export for use in other scripts */
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    SearchHistory,
    MiniPlayer,
    PlaylistCollaboration,
    SocialFeatures,
    OfflineMode,
    TrackLyrics,
    AudioVisualizer,
    PlaybackAnalytics,
    SmartQueue,
  };
}
