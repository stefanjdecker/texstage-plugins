// SPDX-License-Identifier: Apache-2.0
import fs from 'node:fs';
import assert from 'node:assert/strict';
const config=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const {conforms}=await import(config.module);
for(const row of config.cases)assert.equal(conforms(row.schema,row.value),row.expected);
console.log('Checked '+config.cases.length+' transaction role contract cases.');
