import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import fs from 'fs';

export async function GET() {
    try {
        const scriptPath = path.join(process.cwd(), 'scripts', 'get_fm_fields.py');
        const venvPythonPath = path.join(process.cwd(), '.venv', 'Scripts', 'python.exe');
        const pythonCommand = fs.existsSync(venvPythonPath) ? `"${venvPythonPath}"` : 'python';
        const command = `${pythonCommand} "${scriptPath}"`;
        return new Promise((resolve) => {
            exec(command, { timeout: 120000 }, (error, stdout, stderr) => {
                if (stderr) console.error('Get Fields Stderr:', stderr);
                if (error) {
                    resolve(NextResponse.json({ success: false, error: error.message, log: stdout }, { status: 500 }));
                } else {
                    try {
                        const result = JSON.parse(stdout.trim());
                        resolve(NextResponse.json(result));
                    } catch (e) {
                        resolve(NextResponse.json({ success: true, log: stdout }));
                    }
                }
            });
        });
    } catch (err: any) {
        return NextResponse.json({ success: false, error: err.message }, { status: 500 });
    }
}
