
function scrollToSection(id) {
    const section = document.getElementById(id);
    if (section) {
        section.scrollIntoView({ behavior: 'smooth' });
    }
}

// Copy CLI output
document.getElementById("copy-btn").addEventListener("click", () => {
    const code = document.getElementById("cli-output").innerText;
    navigator.clipboard.writeText(code).then(() => {
        alert("CLI output copied to clipboard!");
    });
});
