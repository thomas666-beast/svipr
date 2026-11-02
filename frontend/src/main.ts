// frontend/src/main.ts
import '@fontsource/jetbrains-mono/400.css'; // Regular weight
import '@fontsource/jetbrains-mono/700.css'; // Bold weight

import './style.css'; // Your existing styles

const BANNER = String.raw`
███████╗██╗   ██╗██╗██████╗ ██████╗ 
██╔════╝██║   ██║██║██╔══██╗██╔══██╗
███████╗██║   ██║██║██████╔╝██████╔╝
╚════██║╚██╗ ██╔╝██║██╔═══╝ ██╔══██╗
███████║ ╚████╔╝ ██║██║     ██║  ██║
╚══════╝  ╚═══╝  ╚═╝╚═╝     ╚═╝  ╚═╝
`;

let MAX_SIZE = 4 * 1024 * 1024 * 1024;

let ACCESS_KEY = localStorage.getItem('svipr_key') || '';

const banner = document.getElementById('banner')!;
const dropZone = document.getElementById('drop-zone')!;
const fileInput = document.getElementById('file-input') as HTMLInputElement;
const progress = document.getElementById('progress')!;
const progressBar = document.getElementById('progress-bar')!;
const progressText = document.getElementById('progress-text')!;
const result = document.getElementById('result')!;
const shareLink = document.getElementById('share-link')!;
const curlExample = document.getElementById('curl-example')!;
const errorBox = document.getElementById('error')!;

const donateContainer = document.getElementById('donate-container')!;
const donateModal = document.getElementById('donate-modal')!;
const donateLink = document.getElementById('donate-link')!;
const closeModal = document.getElementById('close-modal')!;

banner.textContent = BANNER.trim();


function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 ** 2) return `${(n / 1024).toFixed(1)} KB`;
  if (n < 1024 ** 3) return `${(n / 1024 ** 2).toFixed(1)} MB`;
  return `${(n / 1024 ** 3).toFixed(2)} GB`;
}


(async () => {
  try {
    const r = await fetch('/api/health');
    if (!r.ok) return;
    const cfg = await r.json();

    // Inside the health fetch try block
    if (cfg.donate === 1) {
      donateContainer.style.display = 'block';
      
      // If you are serving the HTML directly from FastAPI, you could use Jinja2.
      // Since we are using static Vite, we inject the addresses dynamically here:
      // (You'll need to expose donate_btc, donate_xmr, donate_usdt in /api/health to do this)
      const addresses = {
        btc: cfg.donate_btc || "Not set",
        xmr: cfg.donate_xmr || "Not set",
        usdt: cfg.donate_usdt || "Not set"
      };
      
      document.querySelectorAll('.crypto-addr').forEach((el, index) => {
        const addr = [addresses.btc, addresses.xmr, addresses.usdt][index];
        el.textContent = addr;
        (el as HTMLElement).dataset.addr = addr;
      });
    }

    const hint = document.querySelector<HTMLElement>('.drop-zone .hint');

    if (hint && cfg.max_file_size) {
      hint.textContent = `max ${formatBytes(cfg.max_file_size)} · expires in ${cfg.retention_days} days`;
    }

    if (cfg.with_key === 1) {
      const authBox = document.getElementById('auth-box')!;
      const authInput = document.getElementById('auth-input') as HTMLInputElement;
      
      authBox.style.display = 'block';
      authInput.value = ACCESS_KEY;

      authInput.addEventListener('input', (e) => {
        ACCESS_KEY = (e.target as HTMLInputElement).value.trim();
        localStorage.setItem('svipr_key', ACCESS_KEY);
      });
    }
  } catch (err) {
    console.error("Failed to fetch config:", err);
  }
})();

// Modal Logic
donateLink.addEventListener('click', (e) => {
  e.preventDefault();
  donateModal.style.display = 'flex';
});

closeModal.addEventListener('click', () => {
  donateModal.style.display = 'none';
});

// Click outside to close
donateModal.addEventListener('click', (e) => {
  if (e.target === donateModal) donateModal.style.display = 'none';
});

// Copy to clipboard
document.querySelectorAll('.crypto-addr').forEach((el) => {
  el.addEventListener('click', async () => {
    const addr = (el as HTMLElement).dataset.addr;
    if (!addr || addr === 'Not set') return;
    
    await navigator.clipboard.writeText(addr);
    const originalText = el.textContent;
    el.textContent = 'copied to clipboard ✓';
    (el as HTMLElement).classList.add('copied');
    
    setTimeout(() => {
      el.textContent = originalText;
      (el as HTMLElement).classList.remove('copied');
    }, 1500);
  });
});

const origin = location.origin;
document.querySelectorAll<HTMLElement>('.api-block code').forEach((el) => {
  el.textContent = el.textContent!.replaceAll('https://svipr.example', origin);
});


dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  const file = e.dataTransfer?.files[0];
  if (file) upload(file);
});

fileInput.addEventListener('change', () => {
  const file = fileInput.files?.[0];
  if (file) upload(file);
});

function showError(msg: string) {
  errorBox.textContent = msg;
  errorBox.hidden = false;
}

function clearState() {
  errorBox.hidden = true;
  result.hidden = true;
  progress.hidden = true;
  progressText.hidden = true;
  progressBar.style.width = '0%';
}

async function upload(file: File) {
  clearState();

  if (file.size > MAX_SIZE) {
    showError(`file too large: ${file.size} bytes (max ${MAX_SIZE})`);
    return;
  }

  const form = new FormData();
  form.append('file', file);

  progress.hidden = false;
  progressText.hidden = false;

  try {
    const id = await new Promise<string>((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', '/upload');
      
      if (ACCESS_KEY) {
        xhr.setRequestHeader('X-Svipr-Key', ACCESS_KEY);
      }

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          progressBar.style.width = `${(e.loaded / e.total) * 100}%`;
          progressText.textContent = `${formatBytes(e.loaded)} / ${formatBytes(e.total)}`;
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const data = JSON.parse(xhr.responseText);
          resolve(data.id);
        } else {
          reject(new Error(`upload failed: ${xhr.status} ${xhr.responseText}`));
        }
      });

      xhr.addEventListener('error', () => reject(new Error('network error')));
      xhr.send(form);
    });

    const url = `${location.origin}/download/${id}`;
    shareLink.textContent = url;
    shareLink.onclick = async () => {
      await navigator.clipboard.writeText(url);
      const prev = shareLink.textContent;
      shareLink.textContent = 'copied to clipboard ✓';
      setTimeout(() => { shareLink.textContent = prev; }, 1500);
    };

    curlExample.textContent = `curl -F "file=@${file.name}" ${location.origin}/upload`;
    result.hidden = false;
  } catch (err) {
    const msg = (err as Error).message;
    if (msg.includes('429')) {
      showError('too many uploads — slow down and try again in minutes, hours, days or maybe years 😈');
    } else if (msg.includes('401') || msg.includes('403')) {
      showError('access denied — invalid or missing key');
    } else if (msg.includes('413')) {
      showError(`file too large — max is ${formatBytes(MAX_SIZE)}`);
    } else {
      showError(msg);
    }
  } finally {
    progress.hidden = true;
  }
}
