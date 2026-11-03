// Copy the agent's run files (output/runs/*.json) into static/runs/ for the dashboard to read.
import { copyFileSync, existsSync, mkdirSync, readdirSync, rmSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const source = join(here, '..', '..', 'output', 'runs');
const target = join(here, '..', 'static', 'runs');

rmSync(target, { recursive: true, force: true });
mkdirSync(target, { recursive: true });
const files = existsSync(source) ? readdirSync(source).filter((f) => f.endsWith('.json')) : [];
for (const file of files) {
	copyFileSync(join(source, file), join(target, file));
}
console.log(
	files.length
		? `Synced ${files.length} run file(s) into static/runs/`
		: 'No run files in output/runs/ yet. Run `margin-watch run` first.'
);
