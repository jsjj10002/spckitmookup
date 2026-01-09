
const fs = require('fs');
const readline = require('readline');
const path = 'backend/data/pc_data_dump.sql';
const outPath = 'sql_map_node.txt';

async function scan() {
    try {
        const fileStream = fs.createReadStream(path);
        const rl = readline.createInterface({
            input: fileStream,
            crlfDelay: Infinity
        });

        let lineNum = 0;
        let out = fs.createWriteStream(outPath);

        for await (const line of rl) {
            lineNum++;
            if (line.trim().toUpperCase().startsWith('CREATE TABLE')) {
                out.write(`Line ${lineNum}: ${line.trim().substring(0, 200)}\n`);
            }
        }
        console.log('Done scanning.');
        out.end();
    } catch (err) {
        console.error('Error:', err);
    }
}

scan();
