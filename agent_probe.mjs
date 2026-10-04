// Bootstrap uses the published acpx runtime; no ACP transport implementation.
import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

const input = JSON.parse(readFileSync(0, 'utf8'));
let runtime;
try {
  const { createAcpRuntime, createAgentRegistry } = await import(
    pathToFileURL(input.runtime).href
  );
  const records = new Map();
  runtime = createAcpRuntime({
    cwd: input.cwd,
    agentRegistry: createAgentRegistry({ overrides: { 'bootstrap-dsh': input.argv } }),
    sessionStore: {
      load: async id => records.get(id),
      save: async record => { records.set(record.acpxRecordId, record); },
    },
    permissionMode: 'deny-all',
    permissionPolicy: { defaultAction: 'deny' },
    nonInteractivePermissions: 'fail',
    agentProcessEnv: { DSH_PERMISSION_MODE: 'read-only' },
    fs: false,
    terminal: false,
    timeoutMs: 25000,
    probeAgent: 'bootstrap-dsh',
  });
  if (!input.inspect) {
    const health = await runtime.doctor();
    if (!health.ok) throw new Error('ACP_HANDSHAKE_FAILED');
    console.log(JSON.stringify({ ok: true, handshake: true }));
  } else {
    const handle = await runtime.ensureSession({
      sessionKey: 'bootstrap-check', agent: 'bootstrap-dsh', mode: 'persistent', cwd: input.cwd,
    });
    const record = [...records.values()].find(r => r.protocolVersion);
    const status = await runtime.getStatus({ handle });
    // Idle cancellation exercises the protocol without a model request.
    await runtime.cancel({ handle, reason: 'bootstrap idle cancellation check' });
    await runtime.close({ handle, reason: 'bootstrap probe complete', discardPersistentState: true });
    console.log(JSON.stringify({
      ok: true, handshake: true, protocolVersion: record?.protocolVersion,
      agentCapabilities: record?.agentCapabilities,
      model: status.models?.currentModelId,
      idleCancel: true,
    }));
  }
} catch (error) {
  // Native startup errors can contain credentials. Never forward raw errors.
  const code = /^[A-Z_]+$/.test(error?.code ?? '') ? error.code : 'ACP_STARTUP_OR_SESSION_FAILED';
  console.log(JSON.stringify({ ok: false, error: code, kind: error?.constructor?.name,
    category: /timeout|timed out/i.test(error?.message ?? '') ? 'timeout' :
      /not a function/i.test(error?.message ?? '') ? 'runtime-api' : 'startup-or-session' }));
  process.exitCode = 1;
} finally {
  await runtime?.shutdown();
}
