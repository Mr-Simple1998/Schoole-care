const fs = require('node:fs');
const path = require('node:path');

const appConfigPath = path.resolve(__dirname, '..', '..', 'project.config.json');
const outputConfigPath = path.resolve(__dirname, '..', 'dist', 'build', 'mp-weixin', 'project.config.json');

const rootConfig = JSON.parse(fs.readFileSync(appConfigPath, 'utf8'));
if (!rootConfig.appid) {
	throw new Error('project.config.json must define an AppID');
}

const outputConfig = { ...rootConfig };
delete outputConfig.miniprogramRoot;
outputConfig.projectname = 'weapp';
fs.writeFileSync(outputConfigPath, `${JSON.stringify(outputConfig, null, 2)}\n`, 'utf8');
console.log(`Synced mp-weixin project config with AppID: ${outputConfig.appid}`);
