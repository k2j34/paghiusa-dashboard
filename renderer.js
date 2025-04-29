window.electronAPI.onPythonOutput((data) => {
    console.log('Received from Python:', data);
  
    if (data.startsWith('in:')) {
      document.getElementById('inCount').innerText = data.replace('in:', '').trim();
    }
    if (data.startsWith('out:')) {
      document.getElementById('outCount').innerText = data.replace('out:', '').trim();
    }
  });
  