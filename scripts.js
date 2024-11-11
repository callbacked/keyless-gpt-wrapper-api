
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

tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        // Hide all setup sections first
        localSetup.style.display = 'none';
        dockerSetup.style.display = 'none';
        dockerLocalSetup.style.display = 'none';
        
        // Show the appropriate section
        if (tab.id === 'localTab') {
            localSetup.style.display = 'block';
        } else if (tab.id === 'dockerTab') {
            dockerSetup.style.display = 'block';
        } else if (tab.id === 'dockerLocalTab') {
            dockerLocalSetup.style.display = 'block';
        }
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