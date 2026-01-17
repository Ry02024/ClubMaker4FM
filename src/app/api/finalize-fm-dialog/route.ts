import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import fs from 'fs';

export async function POST() {
    try {
        const scriptPath = path.join(process.cwd(), 'scripts', 'finalize_fm_dialog.py');
        const venvPythonPath = path.join(process.cwd(), '.venv', 'Scripts', 'python.exe');
        const pythonCommand = fs.existsSync(venvPythonPath) ? `\"${venvPythonPath}\"` : 'python';

        const command = `${pythonCommand} \"${scriptPath}\"`;

        return new Promise((resolve) => {
            exec(command, (error, stdout, stderr) => {
                if (error) {
                    console.error('Finalize Dialog Error:', error);
                    resolve(NextResponse.json({ success: false, error: error.message, details: stdout }, { status: 500 }));
                } else {
                    console.log('Finalize Dialog Success:', stdout);
                    resolve(NextResponse.json({ success: true, details: stdout }));
                }
            });
        });
    } catch (err: any) {
        console.error('Finalize Dialog API Error:', err);
        return NextResponse.json({ success: false, error: err.message }, { status: 500 });
    }
}
