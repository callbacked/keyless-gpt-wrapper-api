window.addEventListener('scroll', () => {
    const header = document.querySelector('header');
    header.classList.toggle('scrolled', window.scrollY > 0);
});

const modelNames = ['LLaMA 3.1 70b', 'GPT-4o Mini', 'Claude 3 Haiku', 'Mixtral 8x7b'];
let currentIndex = 0;
const modelElement = document.getElementById('modelName');

function typeModelName() {
    const modelName = modelNames[currentIndex];
    modelElement.classList.add('typing');
    modelElement.textContent = '';
    let charIndex = 0;

    const typingInterval = setInterval(() => {
        modelElement.textContent += modelName.charAt(charIndex);
        charIndex++;

        if (charIndex === modelName.length) {
            clearInterval(typingInterval);
            setTimeout(() => {
                backspaceModelName();
            }, 1000);
        }
    }, 150);
}

function backspaceModelName() {
    modelElement.classList.remove('typing');
    const modelName = modelNames[currentIndex];
    let charIndex = modelName.length;

    const backspacingInterval = setInterval(() => {
        modelElement.textContent = modelName.substring(0, charIndex - 1);
        charIndex--;

        if (charIndex < 0) {
            clearInterval(backspacingInterval);
            currentIndex = (currentIndex + 1) % modelNames.length;
            setTimeout(typeModelName, 300);
        }
    }, 100);
}

typeModelName();

const tabs = document.querySelectorAll('.tab');
const localSetup = document.getElementById('localSetup');
const dockerSetup = document.getElementById('dockerSetup');
const dockerLocalSetup = document.getElementById('dockerLocalSetup');

const setupCommands = {
    local: {
        base: [
            'git clone https://github.com/callbacked/keyless-gpt-wrapper-api && cd keyless-gpt-wrapper-api',
            'pip install -r requirements.txt',
            'python server.py'
        ],
        tts: [
            'git clone https://github.com/callbacked/keyless-gpt-wrapper-api && cd keyless-gpt-wrapper-api',
            'pip install -r requirements.txt',
            'python server.py --session-id SESSION_ID_HERE'
        ]
    },
    docker: {
        base: ['docker run -d --name keyless -p 1337:1337 callbacked/keyless:latest'],
        tts: ['docker run -d --name keyless -p 1337:1337 -e TIKTOK_SESSION_ID=SESSION_ID_HERE callbacked/keyless:latest']
    },
    dockerLocal: {
        base: [
            'git clone https://github.com/callbacked/keyless-gpt-wrapper-api && cd keyless-gpt-wrapper-api',
            'docker build -t keyless:latest .',
            'docker run -d --name keyless -p 1337:1337 keyless:latest'
        ],
        tts: [
            'git clone https://github.com/callbacked/keyless-gpt-wrapper-api && cd keyless-gpt-wrapper-api',
            'docker build -t keyless:latest .',
            'docker run -d --name keyless -p 1337:1337 -e TIKTOK_SESSION_ID=SESSION_ID_HERE keyless:latest'
        ]
    }
};

function updateSetupCommands(isTTSEnabled) {
    const activeTab = document.querySelector('.tab.active').id;
    let commands;
    let targetDiv;

    switch (activeTab) {
        case 'localTab':
            commands = isTTSEnabled ? setupCommands.local.tts : setupCommands.local.base;
            targetDiv = localSetup;
            break;
        case 'dockerTab':
            commands = isTTSEnabled ? setupCommands.docker.tts : setupCommands.docker.base;
            targetDiv = dockerSetup;
            break;
        case 'dockerLocalTab':
            commands = isTTSEnabled ? setupCommands.dockerLocal.tts : setupCommands.dockerLocal.base;
            targetDiv = dockerLocalSetup;
            break;
    }

    const commandBlocks = targetDiv.querySelectorAll('.command-block pre code');
    commandBlocks.forEach((block, index) => {
        if (commands[index]) {
            block.textContent = commands[index];
        }
    });
}

tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        localSetup.style.display = 'none';
        dockerSetup.style.display = 'none';
        dockerLocalSetup.style.display = 'none';
        
        if (tab.id === 'localTab') {
            localSetup.style.display = 'block';
        } else if (tab.id === 'dockerTab') {
            dockerSetup.style.display = 'block';
        } else if (tab.id === 'dockerLocalTab') {
            dockerLocalSetup.style.display = 'block';
        }

        // Update commands based on current TTS toggle state
        updateSetupCommands(document.getElementById('ttsToggle').checked);
    });
});

document.querySelectorAll('.copy-button').forEach(button => {
    button.addEventListener('click', async () => {
        const commandBlock = button.previousElementSibling;
        const text = commandBlock.textContent;
        try {
            await navigator.clipboard.writeText(text);
            button.textContent = '✓';
            button.classList.add('copied');
            setTimeout(() => {
                button.textContent = '📋';
                button.classList.remove('copied');
            }, 2000);
        } catch (err) {
            console.error('Failed to copy: ', err);
        }
    });
});

// Add TTS toggle functionality
const ttsToggle = document.getElementById('ttsToggle');
ttsToggle.addEventListener('change', () => {
    updateSetupCommands(ttsToggle.checked);
});

const sessionIdInfo = document.querySelector('.session-id-info');

ttsToggle.addEventListener('change', () => {
    updateSetupCommands(ttsToggle.checked);
    
    // Handle session ID info visibility
    if (ttsToggle.checked) {
        sessionIdInfo.style.display = 'block';
        // Small delay to trigger the animation
        setTimeout(() => {
            sessionIdInfo.classList.add('visible');
        }, 50);
    } else {
        sessionIdInfo.classList.remove('visible');
        // Wait for fade out animation before hiding
        setTimeout(() => {
            sessionIdInfo.style.display = 'none';
        }, 300);
    }
});