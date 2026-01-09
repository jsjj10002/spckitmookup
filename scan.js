
const fs = require('fs');
const path = 'backend/data/pc_data_dump.sql';
const stream = fs.createReadStream(path, { encoding: 'utf8' });

let buffer = '';
let lineCount = 0;

stream.on('data', (chunk) => {
    buffer += chunk;
    let lines = buffer.split('\n');
    buffer = lines.pop(); // Keep the last partial line

    lines.forEach((line) => {
        lineCount++;
        if (line.includes('CREATE TABLE')) {
            console.log(`Line ${lineCount}: ${line.substring(0, 100)}`);
        }
    });
});

stream.on('end', () => {
    console.log('Finished');
});
