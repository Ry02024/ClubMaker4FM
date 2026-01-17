import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import fs from 'fs';

export async function POST() {
    const scriptPath = path.join(process.cwd(), 'scripts', 'capture_screen.py');
    const venvPythonPath = path.join(process.cwd(), '.venv', 'Scripts', 'python.exe');
    const pythonCommand = fs.existsSync(venvPythonPath) ? `"${venvPythonPath}"` : 'python';

    if (!fs.existsSync(scriptPath)) {
        return NextResponse.json({ success: false, error: 'Capture script not found' }, { status: 404 });
    }

    const command = `${pythonCommand} "${scriptPath}"`;

    return new Promise((resolve) => {
        exec(command, (error, stdout, stderr) => {
            if (error) {
                console.error('Capture Error:', error);
                resolve(NextResponse.json({ success: false, error: error.message }, { status: 500 }));
                return;
            }
            resolve(NextResponse.json({ success: true, output: stdout }));
        });
    });
}
