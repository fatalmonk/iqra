const json = (body, status) => Response.json(body, { status, headers: { 'Cache-Control': 'no-store' } });

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname !== '/api/parent-responses') return env.ASSETS.fetch(request);
    if (request.method !== 'POST') return json({ error: 'POST required' }, 405);
    if (request.headers.get('Origin') !== url.origin) return json({ error: 'Invalid origin' }, 403);
    if (!request.headers.get('Content-Type')?.startsWith('application/json')) return json({}, 415);
    if (Number(request.headers.get('Content-Length')) > 200000) return json({}, 413);
    let data;
    try {
      const body = await request.text();
      if (body.length > 100000) return json({}, 413);
      data = JSON.parse(body);
    } catch {
      return json({}, 400);
    }
    if (!/^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/i.test(data?.id) ||
        !data.answers || typeof data.answers !== 'object' || Array.isArray(data.answers)) return json({}, 400);
    const entries = Object.entries(data.answers);
    if (!entries.length || entries.length > 21) return json({}, 400);
    const answers = {};
    for (const [key, value] of entries) {
      if (!/^(?:[1-9]|1[0-9]|2[01])$/.test(key) || !value || typeof value.note !== 'string' ||
          value.note.length > 2000 || !Array.isArray(value.choices) || value.choices.length > 3 ||
          value.choices.some(choice => typeof choice !== 'string' || !choice.trim() || choice.length > 300) ||
          !(value.note.trim() || value.choices.length)) return json({}, 400);
      answers[key] = { choices: value.choices, note: value.note.trim() };
    }
    await env.DB.prepare('INSERT INTO parent_responses (id, answers_json) VALUES (?, ?) ON CONFLICT(id) DO NOTHING')
      .bind(data.id, JSON.stringify(answers)).run();
    return json({ saved: true }, 200);
  }
};
