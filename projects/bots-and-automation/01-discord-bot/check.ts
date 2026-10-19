/*
 * Self-check for the Discord Bot project.
 *
 * Run it from your bot's folder (the one with package.json), and give it the
 * module number you just finished:
 *
 *     node check.ts 3
 *
 * (Use 0 right after setup, in Module 00.) It checks that module and every
 * module before it, so you know nothing broke.
 *
 * It also tests the practice problems in each lesson:
 *
 *     node check.ts practice 2        # tests practice_02.ts
 *
 * The checker never connects to Discord and never needs your token. It
 * type-checks your code, loads src/bot.ts and your commands, and sends your
 * bot pretend interactions and messages to see what it replies. Your bot's
 * name, personality, wording and extra commands can be anything you like.
 */

import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readdirSync, readFileSync, rmSync, statSync } from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { basename, join, relative, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

// Node 22.18 is the first 22.x release that runs .ts files without a flag.
const NODE_MIN = [22, 18];
// How long (ms) a command gets to reply before we decide it never will.
const REPLY_WAIT = 3000;
// Whole-check and per-practice-problem time limits (ms).
const CHECK_TIMEOUT = 120_000;
const PRACTICE_TIMEOUT = 5000;
const THIS_FILE = fileURLToPath(import.meta.url);

class CheckFailed extends Error {}
class NotStarted extends Error {}

function fail(message: string): never {
  throw new CheckFailed(message);
}

// The checker prints with this rather than console.log, because console.log
// is switched off while your bot's code runs (so its logging doesn't get mixed
// into the report).
function say(text = ""): void {
  process.stdout.write(text + "\n");
}

function passed(text: string): void {
  say(`  - ${text}`);
}

// ---------------------------------------------------------------------------
// Files and tools in the learner's folder
// ---------------------------------------------------------------------------

let ROOT = process.cwd();

function path(...parts: string[]): string {
  return join(ROOT, ...parts);
}

function readText(file: string): string {
  return readFileSync(file, "utf8");
}

// Every .ts file under a folder (skipping node_modules and hidden folders).
function tsFiles(folder: string): string[] {
  if (!existsSync(folder)) return [];
  const found: string[] = [];
  for (const name of readdirSync(folder)) {
    if (name === "node_modules" || name.startsWith(".")) continue;
    const full = join(folder, name);
    if (statSync(full).isDirectory()) found.push(...tsFiles(full));
    else if (name.endsWith(".ts")) found.push(full);
  }
  return found;
}

// Runs another program and returns what it printed. Used for tsc and node --test.
function run(args: string[], options: { cwd?: string; timeout?: number } = {}) {
  const result = spawnSync(process.execPath, args, {
    cwd: options.cwd ?? ROOT,
    encoding: "utf8",
    timeout: options.timeout ?? 60_000,
    env: { ...process.env, NODE_NO_WARNINGS: "1", FORCE_COLOR: "0", NO_COLOR: "1" },
  });
  return {
    code: result.status,
    timedOut: result.error !== undefined && (result.error as NodeJS.ErrnoException).code === "ETIMEDOUT",
    output: `${result.stdout ?? ""}${result.stderr ?? ""}`.trim(),
  };
}

function tscPath(): string {
  const tsc = path("node_modules", "typescript", "bin", "tsc");
  if (!existsSync(tsc)) {
    fail("TypeScript isn't installed in this folder. Run:\n    npm install --save-dev typescript @types/node");
  }
  return tsc;
}

// Shows the first few lines of a long output, so a failure message stays readable.
function firstLines(text: string, count = 12): string {
  const lines = text.split("\n");
  const shown = lines.slice(0, count).map((line) => "    " + line).join("\n");
  return lines.length > count ? `${shown}\n    ... (${lines.length - count} more lines)` : shown;
}

// ---------------------------------------------------------------------------
// Loading discord.js and the learner's bot
// ---------------------------------------------------------------------------

// discord.js is loaded from YOUR node_modules, so the checker uses exactly the
// same classes your code does.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Any = any;
let discord: Any = null;

function loadDiscord(): Any {
  if (discord) return discord;
  if (!existsSync(path("node_modules", "discord.js"))) {
    fail("discord.js isn't installed in this folder. Run:\n    npm install discord.js");
  }
  discord = createRequire(path("package.json"))("discord.js");
  // Nothing the checker loads may connect to Discord.
  discord.Client.prototype.login = function () {
    throw new Error("check.ts: client.login() was called. Only src/index.ts should log in.");
  };
  return discord;
}

async function importFile(file: string): Promise<Any> {
  try {
    return await withQuietConsole(() => import(pathToFileURL(file).href));
  } catch (error) {
    const err = error as Error;
    if (String(err.message).includes("client.login() was called")) {
      fail(`Loading ${relative(ROOT, file)} tried to log in to Discord.\n` +
        "Only src/index.ts should call client.login(). The checker loads your other files without connecting.");
    }
    fail(`Couldn't load ${relative(ROOT, file)}:\n${firstLines(err.stack ?? String(err), 8)}`);
  }
}

// Silences console.log/error/warn while your bot's code runs, and keeps what
// it printed in case a failure message needs it.
let captured: string[] = [];
async function withQuietConsole<T>(work: () => Promise<T>): Promise<T> {
  const saved = { log: console.log, error: console.error, warn: console.warn, info: console.info };
  const keep = (...parts: unknown[]) => {
    captured.push(parts.map((p) => (p instanceof Error ? p.stack ?? p.message : String(p))).join(" "));
  };
  console.log = console.error = console.warn = console.info = keep;
  try {
    return await work();
  } finally {
    Object.assign(console, saved);
  }
}

let botClient: Any = null;

// Loads src/bot.ts and calls createBot() once; later checks reuse the client.
async function getBot(): Promise<Any> {
  if (botClient) return botClient;
  const { Client } = loadDiscord();
  const file = path("src", "bot.ts");
  if (!existsSync(file)) fail("Couldn't find src/bot.ts. Module 00 sets it up.");
  const mod = await importFile(file);
  if (typeof mod.createBot !== "function") {
    fail("src/bot.ts should export a function called createBot().");
  }
  let client: Any;
  try {
    client = await withQuietConsole(() => withTimeout(Promise.resolve(mod.createBot()), 10_000, "createBot() took more than 10 seconds."));
  } catch (error) {
    const err = error as Error;
    if (String(err.message).includes("client.login() was called")) {
      fail("createBot() logged in. It should only build and return the client; src/index.ts logs in.");
    }
    if (err instanceof CheckFailed) throw err;
    fail(`createBot() crashed:\n${firstLines(err.stack ?? String(err), 8)}`);
  }
  if (!(client instanceof Client)) {
    fail("createBot() should return the Client it made (a discord.js Client).");
  }
  botClient = client;
  return client;
}

function withTimeout<T>(promise: Promise<T>, ms: number, message: string): Promise<T> {
  return new Promise((resolvePromise, reject) => {
    const timer = setTimeout(() => reject(new CheckFailed(message)), ms);
    promise.then(
      (value) => { clearTimeout(timer); resolvePromise(value); },
      (error) => { clearTimeout(timer); reject(error); },
    );
  });
}

interface LoadedCommand {
  file: string;
  json: Any;
}

let commandCache: LoadedCommand[] | null = null;

// Imports every file in src/commands/ and reads its command data.
async function getCommands(): Promise<LoadedCommand[]> {
  if (commandCache) return commandCache;
  const folder = path("src", "commands");
  const files = existsSync(folder)
    ? readdirSync(folder).filter((name) => name.endsWith(".ts")).sort().map((name) => join(folder, name))
    : [];
  const commands: LoadedCommand[] = [];
  for (const file of files) {
    const mod = await importFile(file);
    const command = mod.default ?? mod.command ?? mod;
    const where = `src/commands/${basename(file)}`;
    if (!command || typeof command.execute !== "function" || !command.data) {
      fail(`${where} should export a command: an object with data and execute, like\n` +
        "    export default { data, execute } satisfies Command;\n" +
        "Keep helper code that isn't a command in src/lib/.");
    }
    if (typeof command.data.toJSON !== "function") {
      fail(`In ${where}, data should be a SlashCommandBuilder.`);
    }
    let json: Any;
    try {
      json = command.data.toJSON();
    } catch (error) {
      fail(`In ${where}, discord.js rejected the command data:\n    ${(error as Error).message.split("\n")[0]}\n` +
        "Every command (and every option) needs setName() with a lowercase name and setDescription() with some text.");
    }
    commands.push({ file: where, json });
  }
  commandCache = commands;
  return commands;
}

async function findCommand(name: string, module: string): Promise<LoadedCommand> {
  const command = (await getCommands()).find((c) => c.json.name === name);
  if (!command) fail(`Couldn't find a /${name} command in src/commands/. ${module} adds it.`);
  return command;
}

// ---------------------------------------------------------------------------
// Pretend Discord: users, interactions and messages
// ---------------------------------------------------------------------------

let nextSnowflake = 1_300_000_000_000_000_000n;
function snowflake(): string {
  nextSnowflake += 1n;
  return String(nextSnowflake);
}

// Everything the checker fakes is wrapped in one of these. If your code reads
// a property the checker doesn't fake, it gets undefined, and the name is
// noted so a failure message can tell you.
let unfaked = new Set<string>();
const IGNORED_KEYS = new Set(["then", "toJSON", "constructor", "asymmetricMatch", "nodeType", "inspect", "valueOf", "length"]);

function strict<T extends object>(label: string, target: T): T {
  return new Proxy(target, {
    get(object, key, receiver) {
      if (typeof key === "symbol" || key in object) return Reflect.get(object, key, receiver);
      if (!IGNORED_KEYS.has(key)) unfaked.add(`${label}.${key}`);
      return undefined;
    },
  });
}

interface FakeUser {
  id: string;
  username: string;
  bot: boolean;
}

function makeUser(name: string, bot = false): Any {
  const id = snowflake();
  return strict("user", {
    id, username: name.toLowerCase(), globalName: name, displayName: name, tag: name.toLowerCase(),
    discriminator: "0", bot, system: false, createdTimestamp: Date.now() - 1e10,
    toString: () => `<@${id}>`,
    displayAvatarURL: () => `https://cdn.discordapp.com/embed/avatars/0.png`,
    avatarURL: () => null,
  });
}

const GUILD_ID = snowflake();
const CHANNEL_ID = snowflake();

function makeMember(user: Any): Any {
  return strict("member", {
    id: user.id, user, displayName: user.displayName, nickname: null, joinedTimestamp: Date.now() - 1e9,
    toString: () => `<@${user.id}>`,
    displayAvatarURL: () => user.displayAvatarURL(),
  });
}

function makeGuild(): Any {
  return strict("guild", { id: GUILD_ID, name: "Check Server", memberCount: 3, toString: () => "Check Server" });
}

function makeChannel(): Any {
  return strict("channel", {
    id: CHANNEL_ID, name: "general", type: 0,
    toString: () => `<#${CHANNEL_ID}>`,
    send: async (payload: unknown) => { recordCall("channel.send", payload); return makeMessage(payload); },
    isTextBased: () => true, isSendable: () => true,
  });
}

// What your bot sent: which method, and the message it built.
interface Call {
  method: string;
  payload: Payload;
}

interface Payload {
  content: string;
  embeds: Any[];
  components: Any[];
  ephemeral: boolean;
}

let calls: Call[] = [];
let escaped: string[] = [];
// Replies discord.js would have refused, because the interaction was already answered.
let refused: string[] = [];

function recordCall(method: string, raw: unknown): Payload {
  const payload = normalize(raw);
  calls.push({ method, payload });
  return payload;
}

// Turns anything you can pass to reply() into one plain shape.
function normalize(raw: unknown): Payload {
  const { MessageFlagsBitField, MessageFlags } = loadDiscord();
  if (typeof raw === "string") return { content: raw, embeds: [], components: [], ephemeral: false };
  const options = (raw ?? {}) as Any;
  const toJSON = (item: Any) => (item && typeof item.toJSON === "function" ? item.toJSON() : item);
  let flags = 0;
  try {
    flags = Number(MessageFlagsBitField.resolve(options.flags ?? 0));
  } catch {
    flags = 0;
  }
  return {
    content: typeof options.content === "string" ? options.content : "",
    embeds: (options.embeds ?? []).map(toJSON),
    components: (options.components ?? []).map(toJSON),
    ephemeral: options.ephemeral === true || (flags & MessageFlags.Ephemeral) !== 0,
  };
}

// Every piece of text in a reply: content plus all embed text.
function textOf(payload: Payload): string {
  const parts = [payload.content];
  for (const embed of payload.embeds) {
    parts.push(embed.title ?? "", embed.description ?? "", embed.footer?.text ?? "", embed.author?.name ?? "");
    for (const field of embed.fields ?? []) parts.push(field.name ?? "", field.value ?? "");
  }
  return parts.join("\n");
}

function buttonsOf(payload: Payload): Any[] {
  const buttons: Any[] = [];
  for (const row of payload.components) {
    for (const component of row.components ?? []) if (component.type === 2) buttons.push(component);
  }
  return buttons;
}

function makeMessage(raw: unknown, author: Any = null): Any {
  const payload = normalize(raw);
  const id = snowflake();
  return strict("message", {
    id, content: payload.content, embeds: payload.embeds, components: payload.components,
    author, channelId: CHANNEL_ID, guildId: GUILD_ID, createdTimestamp: Date.now(),
    edit: async (next: unknown) => { recordCall("message.edit", next); return makeMessage(next, author); },
    delete: async () => undefined,
    url: `https://discord.com/channels/${GUILD_ID}/${CHANNEL_ID}/${id}`,
  });
}

function alreadyReplied(method: string): Error {
  refused.push(method);
  const error = new Error("The reply to this interaction has already been sent or deferred.");
  (error as Any).code = "InteractionAlreadyReplied";
  return error;
}

function notReplied(): Error {
  const error = new Error("The reply to this interaction has not been sent or deferred.");
  (error as Any).code = "InteractionNotReplied";
  return error;
}

// The parts of an interaction for replying, shared by commands and buttons.
// They follow discord.js's rules: one reply (or defer) per interaction, and
// editReply/followUp only after it.
function responseMethods(state: Any) {
  return {
    async reply(raw: unknown) {
      if (state.replied || state.deferred) throw alreadyReplied("reply");
      state.replied = true;
      const payload = recordCall("reply", raw);
      state.ephemeral = payload.ephemeral;
      state.message = makeMessage(raw, state.client.user);
      return strict("response", { id: state.message.id, interaction: state, fetch: async () => state.message, resource: { message: state.message } });
    },
    async deferReply(raw: unknown) {
      if (state.replied || state.deferred) throw alreadyReplied("deferReply");
      state.deferred = true;
      state.ephemeral = recordCall("deferReply", raw).ephemeral;
      return strict("response", { id: snowflake(), interaction: state });
    },
    async editReply(raw: unknown) {
      if (!state.replied && !state.deferred) throw notReplied();
      state.replied = true;
      recordCall("editReply", raw);
      state.message = makeMessage(raw, state.client.user);
      return state.message;
    },
    async followUp(raw: unknown) {
      if (!state.replied && !state.deferred) throw notReplied();
      recordCall("followUp", raw);
      return makeMessage(raw, state.client.user);
    },
    async deleteReply() {
      if (!state.replied && !state.deferred) throw notReplied();
      return undefined;
    },
    async fetchReply() {
      if (!state.message) throw notReplied();
      return state.message;
    },
    isRepliable: () => true,
    inGuild: () => true,
    inCachedGuild: () => true,
    inRawGuild: () => false,
  };
}

// interaction.options: the getters discord.js provides, with the same
// "required" behaviour (asking for a missing required option throws).
function makeOptions(values: Record<string, unknown>): Any {
  const get = (name: string, required = false) => {
    const value = values[name];
    if (value === undefined || value === null) {
      if (required) {
        const error = new TypeError(`Required option "${name}" not found.`);
        (error as Any).code = "CommandInteractionOptionNotFound";
        throw error;
      }
      return null;
    }
    return value;
  };
  return strict("interaction.options", {
    get: (name: string, required = false) => {
      const value = get(name, required);
      return value === null ? null : { name, value };
    },
    getString: get, getInteger: get, getNumber: get, getBoolean: get,
    getUser: get, getChannel: get, getRole: get, getMentionable: get, getAttachment: get,
    getMember: (name: string) => {
      const user = values[name] as Any;
      return user ? makeMember(user) : null;
    },
    getSubcommand: (required = true) => {
      const value = values.__subcommand;
      if (value === undefined && required) throw new TypeError("A subcommand was not selected.");
      return value ?? null;
    },
    getSubcommandGroup: () => values.__group ?? null,
    getFocused: () => "",
    data: [],
  });
}

function baseInteraction(client: Any, user: Any) {
  return {
    id: snowflake(), applicationId: client.user?.id ?? snowflake(), token: "fake-token",
    user, member: makeMember(user), guild: makeGuild(), guildId: GUILD_ID,
    channel: makeChannel(), channelId: CHANNEL_ID, client, locale: "en-US", guildLocale: "en-US",
    createdTimestamp: Date.now(), createdAt: new Date(),
    replied: false, deferred: false, ephemeral: null as boolean | null, message: null as Any,
    isChatInputCommand: () => false, isCommand: () => false, isButton: () => false,
    isAutocomplete: () => false, isMessageComponent: () => false, isModalSubmit: () => false,
    isStringSelectMenu: () => false, isAnySelectMenu: () => false, isContextMenuCommand: () => false,
    isUserContextMenuCommand: () => false, isMessageContextMenuCommand: () => false,
    isPrimaryEntryPointCommand: () => false,
  };
}

function makeCommandInteraction(client: Any, user: Any, name: string, values: Record<string, unknown>): Any {
  const state: Any = baseInteraction(client, user);
  Object.assign(state, {
    type: 2, commandName: name, commandId: snowflake(), commandType: 1, commandGuildId: GUILD_ID,
    options: makeOptions(values),
    isChatInputCommand: () => true, isCommand: () => true,
    showModal: async () => { recordCall("showModal", {}); },
  }, responseMethods(state));
  return strict("interaction", state);
}

function makeButtonInteraction(client: Any, user: Any, customId: string, message: Any): Any {
  const state: Any = baseInteraction(client, user);
  Object.assign(state, {
    type: 3, customId, componentType: 2, message,
    isButton: () => true, isMessageComponent: () => true,
  }, responseMethods(state));
  state.update = async (raw: unknown) => {
    if (state.replied || state.deferred) throw alreadyReplied("update");
    state.replied = true;
    recordCall("update", raw);
    return strict("response", { id: snowflake(), interaction: state });
  };
  state.deferUpdate = async () => {
    if (state.replied || state.deferred) throw alreadyReplied("deferUpdate");
    state.deferred = true;
    recordCall("deferUpdate", {});
    return strict("response", { id: snowflake(), interaction: state });
  };
  return strict("interaction", state);
}

function makeIncomingMessage(client: Any, author: Any, content: string): Any {
  const id = snowflake();
  return strict("message", {
    id, content, author, member: author.bot ? null : makeMember(author), client,
    guild: makeGuild(), guildId: GUILD_ID, channel: makeChannel(), channelId: CHANNEL_ID,
    createdTimestamp: Date.now(), createdAt: new Date(), system: false, webhookId: null,
    mentions: strict("message.mentions", { users: new (loadDiscord().Collection)(), has: () => false }),
    inGuild: () => true,
    reply: async (raw: unknown) => { recordCall("message.reply", raw); return makeMessage(raw, client.user); },
    react: async () => undefined,
  });
}

// What happened when the checker sent one interaction or message.
interface Outcome {
  calls: Call[];
  refused: string[];
  escaped: string[];
  unfaked: string[];
  logs: string[];
}

// Sends one event to your client, the way discord.js would, then waits for
// your listeners to finish replying.
async function deliver(eventName: string, event: Any, waitForReply: boolean): Promise<Outcome> {
  const client = await getBot();
  calls = [];
  escaped = [];
  refused = [];
  unfaked = new Set();
  captured = [];
  const onRejection = (reason: unknown) => {
    escaped.push(reason instanceof Error ? reason.stack ?? reason.message : String(reason));
  };
  process.on("unhandledRejection", onRejection);
  process.on("uncaughtException", onRejection);
  await withQuietConsole(async () => {
    try {
      client.emit(eventName, event);
    } catch (error) {
      onRejection(error);
    }
    const deadline = Date.now() + REPLY_WAIT;
    const answered = () => calls.some((c) => c.method !== "deferReply" && c.method !== "deferUpdate");
    while (waitForReply && Date.now() < deadline && !answered() && escaped.length === 0) await sleep(10);
    // A little extra time, to catch a second reply or an error after the first.
    await sleep(waitForReply ? 60 : 120);
  });
  process.off("unhandledRejection", onRejection);
  process.off("uncaughtException", onRejection);
  return { calls, refused: [...refused], escaped: [...escaped], unfaked: [...unfaked], logs: [...captured] };
}

function sleep(ms: number): Promise<void> {
  return new Promise((done) => setTimeout(done, ms));
}

// Tells you which pretend parts your code reached for, if any.
function unfakedNote(outcome: Outcome): string {
  if (outcome.unfaked.length === 0) return "";
  return "\n\nNote: your code used " + outcome.unfaked.join(", ") +
    ", which the checker doesn't fake. Stick to the parts of the interaction the lessons use, " +
    "or tell the club so the checker can learn them.";
}

function describeEscape(outcome: Outcome): string {
  return firstLines(outcome.escaped[0] ?? "", 8);
}

interface Invocation {
  name: string;
  values?: Record<string, unknown>;
  user?: Any;
}

// Runs one slash command through your bot's interactionCreate listener.
async function invoke(inv: Invocation): Promise<Outcome & { label: string }> {
  const client = await getBot();
  const user = inv.user ?? USER_A;
  const values = inv.values ?? {};
  const interaction = makeCommandInteraction(client, user, inv.name, values);
  const outcome = await deliver(loadDiscord().Events.InteractionCreate, interaction, true);
  const shown = Object.entries(values)
    .filter(([key]) => !key.startsWith("__"))
    .map(([key, value]) => `${key}:${typeof value === "object" ? "@" + (value as Any).displayName : value}`);
  const sub = values.__subcommand ? ` ${values.__subcommand}` : "";
  return { ...outcome, label: `/${inv.name}${sub}${shown.length ? " " + shown.join(" ") : ""}` };
}

// The replies a user would actually see (not the "thinking..." of a defer).
function visible(outcome: Outcome): Call[] {
  return outcome.calls.filter((c) => c.method !== "deferReply" && c.method !== "deferUpdate");
}

// Fails unless the command replied exactly once, without crashing.
function expectOneReply(outcome: Outcome & { label: string }): Payload {
  if (outcome.escaped.length > 0) {
    fail(`${outcome.label} crashed, and the error escaped your interactionCreate listener:\n` +
      describeEscape(outcome) + unfakedNote(outcome));
  }
  const replies = visible(outcome);
  if (replies.length === 0) {
    const deferred = outcome.calls.some((c) => c.method === "deferReply");
    fail(`${outcome.label} never replied${deferred ? " (it deferred, but never called editReply)" : ""}.\n` +
      "Every command must answer with interaction.reply() (or deferReply() then editReply()) " +
      `within 3 seconds, or Discord shows "The application did not respond".` +
      (outcome.logs.length ? `\n\nYour bot printed:\n${firstLines(outcome.logs.join("\n"), 8)}` : "") +
      unfakedNote(outcome));
  }
  if (outcome.refused.length > 0) {
    fail(`${outcome.label} answered the interaction, then called ${outcome.refused[0]}() again. ` +
      "discord.js refuses that with \"The reply to this interaction has already been sent or deferred\". " +
      "Send a second message with followUp(), or change the first with editReply().");
  }
  return replies[0]!.payload;
}

// Sample values for a command's required options, based on their types.
// (The commands the lessons ask for get values that make sense for them.)
const OPTION_SAMPLES: Record<string, Record<string, unknown>> = {
  roll: { dice: "2d6" },
  poll: { question: "Lunch?", options: "pizza, tacos" },
};

function sampleValues(json: Any): Record<string, unknown>[] {
  const options: Any[] = json.options ?? [];
  const subcommands = options.filter((o) => o.type === 1);
  const groups = options.filter((o) => o.type === 2);
  if (groups.length > 0) {
    return groups.flatMap((group) => (group.options ?? []).map((sub: Any) => ({
      __group: group.name, __subcommand: sub.name, ...requiredValues(json.name, sub.options ?? []),
    })));
  }
  if (subcommands.length > 0) {
    return subcommands.map((sub) => ({ __subcommand: sub.name, ...requiredValues(json.name, sub.options ?? []) }));
  }
  return [requiredValues(json.name, options)];
}

function requiredValues(command: string, options: Any[]): Record<string, unknown> {
  const values: Record<string, unknown> = {};
  for (const option of options) {
    if (!option.required) continue;
    const known = OPTION_SAMPLES[command]?.[option.name];
    if (known !== undefined) values[option.name] = known;
    else if (option.choices?.length) values[option.name] = option.choices[0].value;
    else if (option.type === 3) values[option.name] = option.min_length > 4 ? "testing".padEnd(option.min_length, "!") : "test";
    else if (option.type === 4 || option.type === 10) values[option.name] = option.min_value ?? Math.min(1, option.max_value ?? 1);
    else if (option.type === 5) values[option.name] = true;
    else if (option.type === 6 || option.type === 9) values[option.name] = USER_B;
    else if (option.type === 7) values[option.name] = makeChannel();
    else if (option.type === 8) values[option.name] = strict("role", { id: snowflake(), name: "Members", toString: () => "@Members" });
    else values[option.name] = strict("attachment", { id: snowflake(), name: "file.txt", url: "https://example.com/file.txt", size: 10 });
  }
  return values;
}

// Pretend people. USER_C has the same name as USER_A, so their replies can be
// compared with only the ids hidden.
const USER_A = makeUser("Sam");
const USER_B = makeUser("Robin");
const USER_C = makeUser("Sam");
const USER_BOT = makeUser("Sam", true);

// Hides ids, timestamps and other details that differ between two replies.
function masked(payload: Payload): string {
  return JSON.stringify(payload)
    .replace(/\d{17,20}/g, "<id>")
    .replace(/\d{4}-\d\d-\d\dT[\d:.]+Z/g, "<time>");
}

// ---------------------------------------------------------------------------
// The checks for each module
// ---------------------------------------------------------------------------

function typecheck(): void {
  const result = run([tscPath(), "-p", ROOT]);
  if (result.code !== 0) {
    fail("TypeScript found errors. Fix these (run `npx tsc` to see them yourself):\n" + firstLines(result.output, 14));
  }
}

const TOKEN_PATTERN = /[A-Za-z\d_-]{24,28}\.[A-Za-z\d_-]{6}\.[A-Za-z\d_-]{27,40}/;

async function check00(): Promise<void> {
  const [major = 0, minor = 0] = process.versions.node.split(".").map(Number);
  if (major < NODE_MIN[0]! || (major === NODE_MIN[0] && minor < NODE_MIN[1]!)) {
    fail(`You're running Node ${process.versions.node}. This project needs Node 22.18 or newer ` +
      "(24 LTS is best), which runs .ts files directly. See guides/installing-node.md.");
  }
  passed(`Node ${process.versions.node}`);

  if (!existsSync(path("package.json"))) fail("Couldn't find package.json. Run this from your bot's folder.");
  const pkg = JSON.parse(readText(path("package.json")));
  if (pkg.type !== "module") fail('package.json should have "type": "module". Run: npm pkg set type=module');
  loadDiscord();
  tscPath();
  passed("package.json, discord.js and TypeScript are set up");

  if (!existsSync(path("tsconfig.json"))) fail("Couldn't find tsconfig.json. Module 00 shows what goes in it.");
  const config = run([tscPath(), "-p", ROOT, "--showConfig"]);
  let options: Any = {};
  try {
    options = JSON.parse(config.output).compilerOptions ?? {};
  } catch {
    fail("TypeScript couldn't read your tsconfig.json:\n" + firstLines(config.output, 8));
  }
  for (const setting of ["strict", "noEmit", "erasableSyntaxOnly", "allowImportingTsExtensions"]) {
    if (options[setting] !== true) fail(`tsconfig.json should turn on "${setting}": true. Module 00 explains why.`);
  }
  typecheck();
  passed("tsconfig.json is strict, and your code type-checks");

  const ignored = existsSync(path(".gitignore")) ? readText(path(".gitignore")).split(/\r?\n/).map((l) => l.trim()) : [];
  for (const entry of [".env", "node_modules"]) {
    if (!ignored.some((line) => line === entry || line === entry + "/" || line === "/" + entry || line === "/" + entry + "/")) {
      fail(`.gitignore should list ${entry}, so Git never uploads it.`);
    }
  }
  for (const file of [...tsFiles(ROOT), path("package.json")]) {
    if (file === THIS_FILE) continue;
    if (TOKEN_PATTERN.test(readText(file))) {
      fail(`${relative(ROOT, file)} seems to contain a bot token. Tokens belong only in .env.\n` +
        "If that file was ever shared or pushed, reset the token in the Developer Portal now.");
    }
  }
  passed("your token stays out of your code (.env and node_modules are in .gitignore)");

  if (!existsSync(path("src", "index.ts"))) fail("Couldn't find src/index.ts.");
  const index = readText(path("src", "index.ts"));
  if (!index.includes("createBot") || !index.includes(".login(")) {
    fail("src/index.ts should call createBot() and then log in with client.login(process.env.DISCORD_TOKEN).");
  }
  const client = await getBot();
  if (client.listenerCount(loadDiscord().Events.ClientReady) === 0) {
    fail("createBot() should listen for the ClientReady event (client.once(Events.ClientReady, ...)).");
  }
  passed("src/bot.ts builds the client without logging in, and listens for ClientReady");
}

async function check01(): Promise<void> {
  const commands = await getCommands();
  if (commands.length < 2) fail(`Found ${commands.length} command(s) in src/commands/. Module 01 needs at least 2.`);
  const seen = new Map<string, string>();
  for (const { file, json } of commands) {
    if (!json.description) fail(`The command in ${file} needs a description.`);
    const other = seen.get(json.name);
    if (other) fail(`${other} and ${file} are both called /${json.name}. Command names must be unique.`);
    seen.set(json.name, file);
  }
  passed(`found ${commands.length} commands: ${commands.map((c) => "/" + c.json.name).join(", ")}`);

  const deploy = path("src", "deploy-commands.ts");
  if (!existsSync(deploy)) fail("Couldn't find src/deploy-commands.ts, the script that registers your commands.");
  const deployText = readText(deploy);
  if (!deployText.includes("Routes.") || !deployText.includes(".put(")) {
    fail("src/deploy-commands.ts should register the commands with rest.put(Routes.applicationGuildCommands(...), { body }).");
  }
  passed("src/deploy-commands.ts registers commands");

  const client = await getBot();
  if (client.listenerCount(loadDiscord().Events.InteractionCreate) === 0) {
    fail("createBot() should listen for Events.InteractionCreate and run the matching command.");
  }
  for (const { json } of commands) {
    for (const values of sampleValues(json)) expectOneReply(await invoke({ name: json.name, values }));
  }
  passed("every command replies exactly once");

  const unknown = await invoke({ name: "this-command-does-not-exist" });
  if (unknown.escaped.length > 0) {
    fail("A command your bot doesn't have (for example one deleted after it was registered) crashed it:\n" +
      describeEscape(unknown));
  }
  passed("an unknown command doesn't crash the bot");
}

async function check02(): Promise<void> {
  const file = path("src", "lib", "dice.ts");
  if (!existsSync(file)) fail("Couldn't find src/lib/dice.ts.");
  const dice = await importFile(file);
  for (const name of ["parseDice", "rollDice"]) {
    if (typeof dice[name] !== "function") fail(`src/lib/dice.ts should export a function called ${name}().`);
  }
  const good: [string, number, number, number][] = [
    ["d20", 1, 20, 0], ["2d6", 2, 6, 0], ["3d8+2", 3, 8, 2], ["1d4-1", 1, 4, -1],
    ["  2D6  ", 2, 6, 0], ["4d10 + 3", 4, 10, 3], ["100d1000", 100, 1000, 0],
  ];
  for (const [text, count, sides, modifier] of good) {
    let result: Any;
    try {
      result = dice.parseDice(text);
    } catch (error) {
      fail(`parseDice(${JSON.stringify(text)}) threw ${(error as Error).message}. It should return a result instead of throwing.`);
    }
    const want = { ok: true, value: { count, sides, modifier } };
    if (!result?.ok || result.value?.count !== count || result.value?.sides !== sides || result.value?.modifier !== modifier) {
      fail(`parseDice(${JSON.stringify(text)}) returned ${JSON.stringify(result)}, but should return ${JSON.stringify(want)}.`);
    }
  }
  const bad = ["", "banana", "0d6", "2d1", "101d6", "2d1001", "2d", "d", "2d6+", "1.5d6", "-2d6", "2d6++1", "2x6", "d6d6"];
  for (const text of bad) {
    let result: Any;
    try {
      result = dice.parseDice(text);
    } catch (error) {
      fail(`parseDice(${JSON.stringify(text)}) threw "${(error as Error).message}". Bad input should return { ok: false, error } instead.`);
    }
    if (result?.ok !== false || typeof result.error !== "string" || result.error.trim() === "") {
      fail(`parseDice(${JSON.stringify(text)}) returned ${JSON.stringify(result)}. ` +
        "It should return { ok: false, error: <a message for the user> }.");
    }
  }
  passed("parseDice() reads good dice and explains bad ones");

  const rollCases: [Any, () => number, number[], number][] = [
    [{ count: 3, sides: 6, modifier: 2 }, () => 0, [1, 1, 1], 5],
    [{ count: 2, sides: 20, modifier: -1 }, () => 0.9999999, [20, 20], 39],
    [{ count: 1, sides: 10, modifier: 0 }, () => 0.5, [6], 6],
  ];
  for (const [spec, rng, rolls, total] of rollCases) {
    const result = dice.rollDice(spec, rng);
    if (JSON.stringify(result?.rolls) !== JSON.stringify(rolls) || result?.total !== total) {
      fail(`rollDice(${JSON.stringify(spec)}, rng) with an rng that always returns ${rng()} gave ` +
        `${JSON.stringify(result)}, but should give rolls ${JSON.stringify(rolls)} and total ${total}.\n` +
        "Each roll is Math.floor(rng() * sides) + 1.");
    }
  }
  for (let i = 0; i < 50; i++) {
    const { rolls } = dice.rollDice({ count: 5, sides: 4, modifier: 0 });
    if (!rolls.every((r: number) => Number.isInteger(r) && r >= 1 && r <= 4)) {
      fail(`rollDice() with no rng gave ${JSON.stringify(rolls)} for 5d4. Every roll should be a whole number from 1 to 4.`);
    }
  }
  passed("rollDice() rolls fairly, and uses the rng it's given");

  const roll = await findCommand("roll", "Module 02");
  const diceOption = (roll.json.options ?? []).find((o: Any) => o.name === "dice");
  if (!diceOption || diceOption.type !== 3 || !diceOption.required) {
    fail("/roll should have a required string option called dice.");
  }
  for (let i = 0; i < 5; i++) {
    const reply = expectOneReply(await invoke({ name: "roll", values: { dice: "3d6+100" } }));
    const numbers = (textOf(reply).match(/\d+/g) ?? []).map(Number);
    if (!numbers.some((n) => n >= 103 && n <= 118)) {
      fail(`/roll dice:3d6+100 replied:\n    ${textOf(reply)}\nThe reply should include the total (between 103 and 118).`);
    }
  }
  passed("/roll replies with the total");

  const withOptions = (await getCommands()).filter((c) => c.json.name !== "roll" && (c.json.options ?? []).length > 0);
  if (withOptions.length === 0) fail("Your turn in Module 02: add a command of your own (besides /roll) that takes an option.");
  passed(`${withOptions.map((c) => "/" + c.json.name).join(", ")} take options too`);
}

async function check03(): Promise<void> {
  const banana = await invoke({ name: "roll", values: { dice: "banana" } });
  const reply = expectOneReply(banana);
  if (!reply.ephemeral) {
    fail("/roll dice:banana should explain the problem in an ephemeral reply (flags: MessageFlags.Ephemeral), " +
      "so only the person who typed it sees the error.");
  }
  passed("/roll explains bad dice privately");

  // A required option that's missing makes getString(name, true) throw, the
  // same as a bug in a command would. The central handler should catch it.
  const broken = await invoke({ name: "roll", values: {} });
  if (broken.escaped.length > 0) {
    fail("When a command throws an error, it escaped your interactionCreate listener:\n" + describeEscape(broken) +
      "\nWrap command.execute() in try/catch in your listener (Module 03, step 3).");
  }
  const errorReply = visible(broken)[0];
  if (!errorReply) fail("When a command throws an error, your listener should still tell the user something went wrong.");
  if (!errorReply.payload.ephemeral) fail("The \"something went wrong\" message should be ephemeral.");
  passed("a command that throws gets a private error message, and the bot keeps running");

  await findCommand("help", "Module 03");
  const help = expectOneReply(await invoke({ name: "help" }));
  if (help.embeds.length === 0) fail("/help should reply with an embed (EmbedBuilder).");
  const text = textOf(help).toLowerCase();
  const missing = (await getCommands()).map((c) => c.json.name).filter((name: string) => !text.includes(name));
  if (missing.length > 0) {
    fail(`/help doesn't mention ${missing.map((m: string) => "/" + m).join(", ")}. Build the list from your loaded commands, so it's never out of date.`);
  }
  passed("/help lists every command in an embed");
}

// Runs your tests with node --test and returns how many passed.
function runTests(minimum: number): number {
  const files = tsFiles(path("tests")).filter((f) => f.endsWith(".test.ts"));
  if (files.length === 0) fail("Couldn't find any tests. Put them in tests/, in files ending in .test.ts.");
  const result = run(["--test", "--test-reporter=tap"], { timeout: 90_000 });
  if (result.timedOut) fail("Your tests were still running after 90 seconds. Is one of them waiting forever?");
  // The TAP report ends with lines like "# pass 7" and "# fail 0".
  const count = (label: string) => Number(new RegExp(`^# ${label} (\\d+)`, "m").exec(result.output)?.[1] ?? 0);
  const pass = count("pass");
  const failed = count("fail");
  if (failed > 0 || result.code !== 0) {
    const problems = result.output.split("\n").filter((line) => /^\s*not ok|error:|Error|expected|actual/.test(line));
    fail(`${failed || "Some"} of your tests failed. Run \`npm test\` to see them. The first problems:\n` +
      firstLines(problems.join("\n") || result.output, 14));
  }
  if (pass < minimum) fail(`${pass} tests passed. This module needs at least ${minimum}.`);
  return pass;
}

function testsImport(fragment: RegExp): boolean {
  return tsFiles(path("tests")).some((file) => fragment.test(readText(file)));
}

async function check04(): Promise<void> {
  const count = runTests(5);
  passed(`${count} tests pass`);
  if (!testsImport(/from\s+["'][^"']*lib\/dice(\.ts)?["']/)) fail("Write tests for src/lib/dice.ts (import it in a file in tests/).");
  if (!testsImport(/from\s+["'][^"']*commands\/[^"']+["']/)) {
    fail("Write at least one test that runs a command's execute() with a fake interaction (Module 04, step 4).");
  }
  passed("tests cover dice.ts and at least one command");
}

async function check05(): Promise<void> {
  const xpFile = path("src", "lib", "xp.ts");
  const cooldownFile = path("src", "lib", "cooldown.ts");
  if (!existsSync(xpFile)) fail("Couldn't find src/lib/xp.ts.");
  if (!existsSync(cooldownFile)) fail("Couldn't find src/lib/cooldown.ts.");
  const xp = await importFile(xpFile);
  if (typeof xp.levelFor !== "function") fail("src/lib/xp.ts should export a function called levelFor().");
  if (typeof xp.XPStore !== "function") fail("src/lib/xp.ts should export a class called XPStore.");

  let previous = -Infinity;
  for (let points = 0; points <= 200_000; points += points < 1000 ? 7 : 997) {
    const level = xp.levelFor(points);
    if (!Number.isInteger(level) || level < 0) fail(`levelFor(${points}) returned ${level}. Levels should be whole numbers, 0 or more.`);
    if (level < previous) fail(`levelFor(${points}) is ${level}, lower than for less XP. More XP should never lower your level.`);
    previous = level;
  }
  if (xp.levelFor(200_000) <= xp.levelFor(0)) fail("levelFor() never goes up. Your curve should reach higher levels with more XP.");
  passed("levelFor() is a curve that only goes up");

  const folder = mkdtempSync(join(tmpdir(), "xp-"));
  const dbPath = join(folder, "xp.db");
  try {
    const store = new xp.XPStore(dbPath);
    if (store.getXp("1") !== 0) fail(`getXp() for someone with no XP returned ${store.getXp("1")}, but should return 0.`);
    const totals = [store.addXp("1", 10), store.addXp("1", 5), store.addXp("2", 40), store.addXp("3", 20)];
    if (JSON.stringify(totals) !== "[10,15,40,20]") {
      fail(`addXp() should return the user's new total. Adding 10 then 5 to one user, then 40 and 20 to two others, returned ${JSON.stringify(totals)}.`);
    }
    store.close?.();
    const reopened = new xp.XPStore(dbPath);
    if (reopened.getXp("1") !== 15) fail("XP should still be there after the XPStore is closed and opened again on the same file.");
    const board = reopened.leaderboard(2);
    const want = [{ userId: "2", xp: 40 }, { userId: "3", xp: 20 }];
    if (JSON.stringify(board?.map((r: Any) => ({ userId: r.userId, xp: r.xp }))) !== JSON.stringify(want)) {
      fail(`leaderboard(2) returned ${JSON.stringify(board)}, but should return ${JSON.stringify(want)}.`);
    }
    reopened.close?.();
  } catch (error) {
    if (error instanceof CheckFailed) throw error;
    fail(`XPStore crashed:\n${firstLines((error as Error).stack ?? String(error), 8)}`);
  } finally {
    rmSync(folder, { recursive: true, force: true });
  }
  passed("XPStore adds XP, keeps it in the database, and ranks users");

  const { Cooldown } = await importFile(cooldownFile);
  if (typeof Cooldown !== "function") fail("src/lib/cooldown.ts should export a class called Cooldown.");
  let now = 1_000_000;
  const cooldown = new Cooldown(60_000, () => now);
  const steps = [cooldown.tryUse("a"), cooldown.tryUse("a"), cooldown.tryUse("b")];
  now += 59_999;
  steps.push(cooldown.tryUse("a"));
  now += 1;
  steps.push(cooldown.tryUse("a"));
  if (JSON.stringify(steps) !== "[true,false,true,false,true]") {
    fail(`A 60-second Cooldown with a fake clock gave ${JSON.stringify(steps)} for: use a, use a again, use b, ` +
      "59.999 s later use a, 1 ms later use a. It should give [true,false,true,false,true].");
  }
  passed("Cooldown uses the clock it's given");

  const client = await getBot();
  const { Events } = loadDiscord();
  if (client.listenerCount(Events.MessageCreate) === 0) fail("createBot() should listen for Events.MessageCreate to award XP.");
  await findCommand("rank", "Module 05");
  await findCommand("leaderboard", "Module 05");
  const before = masked(expectOneReply(await invoke({ name: "rank", user: USER_A })));
  const human = await deliver(Events.MessageCreate, makeIncomingMessage(client, USER_A, "hello everyone"), false);
  if (human.escaped.length > 0) fail("Your messageCreate listener crashed:\n" + describeEscape(human) + unfakedNote(human));
  for (let i = 0; i < 3; i++) await deliver(Events.MessageCreate, makeIncomingMessage(client, USER_BOT, "beep"), false);
  const after = masked(expectOneReply(await invoke({ name: "rank", user: USER_A })));
  const stranger = masked(expectOneReply(await invoke({ name: "rank", user: USER_C })));
  const robot = masked(expectOneReply(await invoke({ name: "rank", user: USER_BOT })));
  if (after === before || after === stranger) {
    fail("After a user sent a message, their /rank didn't change. Award XP in your messageCreate listener, " +
      "and make /rank show the user's XP.");
  }
  if (robot !== stranger) fail("A bot account sent messages and earned XP. Ignore messages where message.author.bot is true.");
  passed("messages earn XP, bots don't, and /rank shows it");
  expectOneReply(await invoke({ name: "leaderboard" }));
  passed("/leaderboard replies");

  const count = runTests(8);
  passed(`${count} tests pass`);
}

async function check06(): Promise<void> {
  const file = path("src", "lib", "poll.ts");
  if (!existsSync(file)) fail("Couldn't find src/lib/poll.ts.");
  const { Poll } = await importFile(file);
  if (typeof Poll !== "function") fail("src/lib/poll.ts should export a class called Poll.");
  const poll = new Poll("Lunch?", ["pizza", "tacos", "sushi"]);
  const expect = (label: string, got: unknown, want: unknown) => {
    if (JSON.stringify(got) !== JSON.stringify(want)) fail(`${label}: got ${JSON.stringify(got)}, but should be ${JSON.stringify(want)}.`);
  };
  expect("counts() on a new poll", poll.counts(), [0, 0, 0]);
  expect("winners() on a poll with no votes", poll.winners(), []);
  poll.vote("u1", 0);
  poll.vote("u2", 0);
  poll.vote("u3", 1);
  expect("counts() after votes for 0, 0, 1", poll.counts(), [2, 1, 0]);
  expect("winners() after votes for 0, 0, 1", poll.winners(), [0]);
  poll.vote("u1", 1);
  expect("counts() after the first voter changes to 1", poll.counts(), [1, 2, 0]);
  poll.vote("u4", 0);
  expect("winners() when two options tie", poll.winners(), [0, 1]);
  for (const index of [3, -1, 1.5]) {
    let threw = false;
    try {
      poll.vote("u5", index);
    } catch {
      threw = true;
    }
    if (!threw) fail(`poll.vote("u5", ${index}) should throw an error: there's no option ${index}.`);
  }
  expect("counts() after the bad votes", poll.counts(), [2, 2, 0]);
  passed("Poll counts votes, lets people change their vote, and finds winners");

  await findCommand("poll", "Module 06");
  const client = await getBot();
  const { Events } = loadDiscord();
  const start = await invoke({ name: "poll", values: { question: "Lunch?", options: "pizza, tacos, sushi" } });
  const message = expectOneReply(start);
  if (message.ephemeral) fail("The poll itself shouldn't be ephemeral: everyone needs to see it.");
  const buttons = buttonsOf(message);
  if (buttons.length !== 3) fail(`/poll with 3 options sent ${buttons.length} buttons. It should send one per option.`);
  const ids = buttons.map((b) => b.custom_id);
  if (new Set(ids).size !== 3 || ids.some((id) => typeof id !== "string" || id.length > 100)) {
    fail(`The buttons' custom ids should be different from each other and at most 100 characters: ${JSON.stringify(ids)}`);
  }
  for (const [i, option] of ["pizza", "tacos", "sushi"].entries()) {
    if (!String(buttons[i]?.label ?? "").toLowerCase().includes(option)) fail(`Button ${i + 1} should be labelled with "${option}".`);
  }
  passed("/poll sends one button per option");

  for (const options of ["just one", "a, b, c, d, e, f"]) {
    const reply = expectOneReply(await invoke({ name: "poll", values: { question: "Lunch?", options } }));
    if (!reply.ephemeral || buttonsOf(reply).length > 0) {
      fail(`/poll options:"${options}" should be refused with an ephemeral message: polls need 2 to 5 options.`);
    }
  }
  passed("/poll refuses fewer than 2 or more than 5 options");

  const pollMessage = makeMessage({ embeds: message.embeds, components: message.components, content: message.content });
  const click = async (user: Any, customId: string) =>
    deliver(Events.InteractionCreate, makeButtonInteraction(client, user, customId, pollMessage), true);
  const first = await click(USER_A, ids[0]);
  const second = await click(USER_B, ids[1]);
  for (const [who, outcome] of [["The first click", first], ["The second click", second]] as const) {
    if (outcome.escaped.length > 0) fail(`${who} on a poll button crashed:\n${describeEscape(outcome)}${unfakedNote(outcome)}`);
    if (outcome.refused.length > 0) fail(`${who} on a poll button answered, then called ${outcome.refused[0]}() again. Answer each click once.`);
    if (visible(outcome).length === 0 && !outcome.calls.some((c) => c.method === "deferUpdate")) {
      fail(`${who} on a poll button got no response. Route button clicks in your interactionCreate listener ` +
        "(interaction.isButton()) and answer with interaction.update() or interaction.reply()." + unfakedNote(outcome));
    }
  }
  const firstUpdate = first.calls.find((c) => c.method === "update");
  const secondUpdate = second.calls.find((c) => c.method === "update");
  if (firstUpdate && secondUpdate && masked(firstUpdate.payload) === masked(secondUpdate.payload)) {
    fail("Two votes for different options produced the same poll message. The message should show the new counts.");
  }
  passed("clicking a button records the vote and answers");

  const stale = await click(USER_A, "vote:0:0");
  if (stale.escaped.length > 0) fail(`A click on a button your bot doesn't know (for example from before a restart) crashed it:\n${describeEscape(stale)}`);
  passed("an unknown button doesn't crash the bot");
}

const CHECKS = [check00, check01, check02, check03, check04, check05, check06];

// ---------------------------------------------------------------------------
// Practice problems
// ---------------------------------------------------------------------------

type PracticeTest = (p: Practice) => Promise<void>;

// Calls the functions in your practice file.
class Practice {
  readonly mod: Any;
  constructor(mod: Any) {
    this.mod = mod;
  }

  fn(name: string): Any {
    const fn = this.mod[name];
    if (typeof fn !== "function") fail(`Couldn't find ${name}() in the practice file. Keep the names from the file.`);
    return fn;
  }

  // Calls a function (awaiting it if it's async). A TODO error means not started.
  async call(name: string, ...args: unknown[]): Promise<Any> {
    try {
      return await this.fn(name)(...args);
    } catch (error) {
      throw explain(name, error);
    }
  }
}

function explain(name: string, error: unknown): Error {
  if (error instanceof CheckFailed || error instanceof NotStarted) return error;
  if (error instanceof Error && error.message === "TODO") return new NotStarted();
  const message = error instanceof Error ? `${error.name}: ${error.message}` : String(error);
  return new CheckFailed(`${name}() crashed with ${message}`);
}

function show(value: unknown): string {
  if (value instanceof Map) return `Map(${JSON.stringify([...value])})`;
  if (value === undefined) return "undefined";
  if (Number.isNaN(value)) return "NaN";
  return JSON.stringify(value);
}

async function returns(p: Practice, name: string, args: unknown[], want: unknown): Promise<void> {
  const got = await p.call(name, ...args);
  if (show(got) !== show(want)) {
    fail(`${name}(${args.map(show).join(", ")}) returned ${show(got)}, but should return ${show(want)}.`);
  }
}

async function rejects(promise: Promise<unknown>): Promise<unknown> {
  try {
    await promise;
  } catch (error) {
    return error ?? new Error("rejected");
  }
  return null;
}

// --- Module 01 ---------------------------------------------------------------
async function p01Sleep(p: Practice) {
  const started = Date.now();
  await p.call("sleep", 60);
  const took = Date.now() - started;
  if (took < 50) fail(`sleep(60) finished after ${took} ms. It should wait about 60 ms.`);
  if (took > 1000) fail(`sleep(60) took ${took} ms. It should wait about 60 ms.`);
}

async function p01WithTimeout(p: Practice) {
  const later = (ms: number, value: unknown) => new Promise((done) => setTimeout(() => done(value), ms));
  await returns(p, "withTimeout", [later(10, "fast"), 200], "fast");
  const started = Date.now();
  const error = await rejects(p.call("withTimeout", later(1000, "slow"), 50));
  if (error === null) fail("withTimeout(promise, 50) for a promise that takes 1 second should reject.");
  if (error instanceof NotStarted) throw error;
  if (Date.now() - started > 400) fail("withTimeout(promise, 50) should reject after about 50 ms, not wait for the promise.");
  const original = await rejects(p.call("withTimeout", Promise.reject(new Error("boom")), 200));
  if (!(original instanceof Error) || !original.message.includes("boom")) {
    fail("If the promise itself fails, withTimeout() should reject with that same error.");
  }
}

async function p01FetchAll(p: Practice) {
  const delays: Record<string, number> = { a: 120, b: 60, c: 10 };
  const fetchOne = (id: string) => new Promise((done) => setTimeout(() => done(id.toUpperCase()), delays[id]));
  const started = Date.now();
  await returns(p, "fetchAll", [["a", "b", "c"], fetchOne], ["A", "B", "C"]);
  const took = Date.now() - started;
  if (took > 170) fail(`fetchAll() took ${took} ms for fetches of 120, 60 and 10 ms. Run them at the same time, not one after another.`);
  await returns(p, "fetchAll", [[], fetchOne], []);
}

async function p01TotalLength(p: Practice) {
  const fetchText = async (url: string) => `<page ${url}>`;
  await returns(p, "totalLength", [["a", "bb"], fetchText], "<page a>".length + "<page bb>".length);
  await returns(p, "totalLength", [[], fetchText], 0);
}

// --- Module 02 ---------------------------------------------------------------
async function p02ParseDuration(p: Practice) {
  const good: [string, number][] = [["90s", 90], ["5m", 300], ["1h30m", 5400], ["2h", 7200], ["1h 5m 10s", 3910], [" 10M ", 600]];
  for (const [text, seconds] of good) await returns(p, "parseDuration", [text], { ok: true, value: seconds });
  for (const text of ["", "soon", "10", "5x", "m5", "1h1h", "5m1h", "0m"]) {
    const result = await p.call("parseDuration", text);
    if (result?.ok !== false || typeof result.error !== "string" || !result.error) {
      fail(`parseDuration(${show(text)}) returned ${show(result)}, but should return { ok: false, error: "<why>" }.`);
    }
  }
}

async function p02FormatDuration(p: Practice) {
  const cases: [number, string][] = [[5400, "1h 30m"], [90, "1m 30s"], [59, "59s"], [3600, "1h"], [0, "0s"], [3661, "1h 1m 1s"]];
  for (const [seconds, text] of cases) await returns(p, "formatDuration", [seconds], text);
}

async function p02ParseColor(p: Practice) {
  await returns(p, "parseColor", ["#ff8800"], { ok: true, value: 0xff8800 });
  await returns(p, "parseColor", ["FF8800"], { ok: true, value: 0xff8800 });
  await returns(p, "parseColor", ["#fff"], { ok: true, value: 0xffffff });
  await returns(p, "parseColor", ["#1a2"], { ok: true, value: 0x11aa22 });
  for (const text of ["#gggggg", "#12345", "red", "", "#ff88001"]) {
    const result = await p.call("parseColor", text);
    if (result?.ok !== false || !result.error) fail(`parseColor(${show(text)}) returned ${show(result)}, but should be { ok: false, error }.`);
  }
}

async function p02TotalSeconds(p: Practice) {
  await returns(p, "totalSeconds", [["10s", "5s", "1s"]], { ok: true, value: 16 });
  await returns(p, "totalSeconds", [[]], { ok: true, value: 0 });
  const result = await p.call("totalSeconds", ["10s", "oops", "5s"]);
  if (result?.ok !== false || !String(result.error).includes("oops")) {
    fail(`totalSeconds(["10s", "oops", "5s"]) returned ${show(result)}. It should return the error from "oops".`);
  }
}

// --- Module 03 ---------------------------------------------------------------
async function p03ToReply(p: Practice) {
  const { UserError } = p.mod;
  await returns(p, "toReply", [new UserError("You need to be in a server for that.")], "You need to be in a server for that.");
  await returns(p, "toReply", [new TypeError("x is undefined")], "Something went wrong.");
  await returns(p, "toReply", ["a string"], "Something went wrong.");
  await returns(p, "toReply", [undefined], "Something went wrong.");
}

async function p03CooldownError(p: Practice) {
  const { CooldownError, UserError } = p.mod;
  if (typeof CooldownError !== "function") fail("Couldn't find the CooldownError class.");
  let error: Any;
  try {
    error = new CooldownError(5);
  } catch (e) {
    throw explain("CooldownError", e);
  }
  if (!(error instanceof UserError) || !(error instanceof Error)) fail("A CooldownError should also be a UserError (extend it).");
  if (error.message !== "Slow down! Try again in 5s.") fail(`new CooldownError(5).message is ${show(error.message)}, but should be "Slow down! Try again in 5s."`);
  if ((error as Any).seconds !== 5) fail("new CooldownError(5).seconds should be 5.");
  if (error.name !== "CooldownError") fail(`new CooldownError(5).name is ${show(error.name)}, but should be "CooldownError".`);
}

async function p03Truncate(p: Practice) {
  await returns(p, "truncate", ["hello world", 8], "hello...");
  await returns(p, "truncate", ["hello", 5], "hello");
  await returns(p, "truncate", ["hello", 10], "hello");
  await returns(p, "truncate", ["abcdef", 5], "ab...");
  const long = "x".repeat(2500);
  const result = await p.call("truncate", long, 2000);
  if (typeof result !== "string" || result.length !== 2000 || !result.endsWith("...")) {
    fail("truncate() of 2500 characters to 2000 should give exactly 2000 characters, ending in \"...\".");
  }
}

async function p03JsonError(p: Practice) {
  await returns(p, "jsonError", ['{"a": 1}'], null);
  const message = await p.call("jsonError", "{oops");
  if (typeof message !== "string" || message.length === 0) fail(`jsonError("{oops") returned ${show(message)}. It should return the error's message.`);
}

// --- Module 04 ---------------------------------------------------------------
type Clamp = (n: number, lo: number, hi: number) => number;
const CLAMPS: [string, Clamp][] = [
  ["only clamps the top", (n, _lo, hi) => Math.min(n, hi)],
  ["only clamps the bottom", (n, lo) => Math.max(n, lo)],
  ["gets the top edge wrong", (n, lo, hi) => (n >= hi ? hi - 1 : Math.max(n, lo))],
  ["rounds the number", (n, lo, hi) => Math.round(Math.max(lo, Math.min(n, hi)))],
  ["swaps lo and hi", (n, lo, hi) => Math.max(hi, Math.min(n, lo))],
];

async function p04CheckClamp(p: Practice) {
  const good: Clamp = (n, lo, hi) => Math.max(lo, Math.min(n, hi));
  try {
    await p.call("checkClamp", good);
  } catch (error) {
    if (error instanceof NotStarted) throw error;
    fail(`checkClamp() failed a correct clamp. ${(error as Error).message.replace(/^checkClamp\(\) crashed with /, "")}`);
  }
  for (const [label, bad] of CLAMPS) {
    let caught = false;
    try {
      await p.call("checkClamp", bad);
    } catch (error) {
      if (error instanceof NotStarted) throw error;
      caught = true;
    }
    if (!caught) fail(`checkClamp() passed a broken clamp that ${label}. Add a test that catches it.`);
  }
}

async function p04Cooldown(p: Practice) {
  const { Cooldown } = p.mod;
  let now = 0;
  let cooldown: Any;
  try {
    cooldown = new Cooldown(1000, () => now);
  } catch (error) {
    throw explain("Cooldown", error);
  }
  const call = async (method: string, key: string) => {
    try {
      return await cooldown[method](key);
    } catch (error) {
      throw explain(method, error);
    }
  };
  const got = [await call("tryUse", "a"), await call("tryUse", "a"), await call("remaining", "a"), await call("tryUse", "b")];
  now = 999;
  got.push(await call("tryUse", "a"), await call("remaining", "a"));
  now = 1000;
  got.push(await call("tryUse", "a"), await call("remaining", "zzz"));
  const want = [true, false, 1000, true, false, 1, true, 0];
  if (show(got) !== show(want)) {
    fail(`With a 1000 ms Cooldown: tryUse(a), tryUse(a), remaining(a), tryUse(b), at 999 ms tryUse(a), remaining(a), ` +
      `at 1000 ms tryUse(a), remaining(zzz) gave ${show(got)}, but should give ${show(want)}.`);
  }
}

async function p04SequenceRng(p: Practice) {
  const rng = await p.call("makeSequenceRng", [0.1, 0.5, 0.9]);
  if (typeof rng !== "function") fail("makeSequenceRng() should return a function.");
  const got = [rng(), rng(), rng(), rng(), rng()];
  if (show(got) !== show([0.1, 0.5, 0.9, 0.1, 0.5])) fail(`Calling the rng 5 times gave ${show(got)}, but should give [0.1,0.5,0.9,0.1,0.5].`);
}

async function p04NewSettings(p: Practice) {
  const first = await p.call("newSettings");
  first.prefix = "?";
  first.tags.push("music");
  const second = await p.call("newSettings");
  if (show(second) !== show({ prefix: "!", tags: ["new"] })) {
    fail(`After one server changed its settings, newSettings() for another server returned ${show(second)}. ` +
      "Each server should get its own fresh copy.");
  }
}

// --- Module 05 ---------------------------------------------------------------
async function freshDb(p: Practice): Promise<Any> {
  const { DatabaseSync } = await import("node:sqlite");
  const db = new DatabaseSync(":memory:");
  try {
    p.fn("setup")(db);
  } catch (error) {
    throw explain("setup", error);
  }
  return db;
}

async function p05Notes(p: Practice) {
  const db = await freshDb(p);
  const ids = [await p.call("addNote", db, "u1", "buy milk"), await p.call("addNote", db, "u2", "hi"), await p.call("addNote", db, "u1", "walk dog")];
  if (!ids.every((id) => typeof id === "number") || new Set(ids).size !== 3) {
    fail(`addNote() should return each new note's id as a number. It returned ${show(ids)}.`);
  }
  await returns(p, "notesFor", [db, "u1"], ["buy milk", "walk dog"]);
  await returns(p, "notesFor", [db, "nobody"], []);
}

async function p05AddPoints(p: Practice) {
  const db = await freshDb(p);
  await returns(p, "addPoints", [db, "u1", 10], 10);
  await returns(p, "addPoints", [db, "u1", 5], 15);
  await returns(p, "addPoints", [db, "u2", 3], 3);
  const rows = db.prepare("SELECT COUNT(*) AS n FROM scores").get();
  if (rows.n !== 2) fail(`After adding points for 2 users there are ${rows.n} rows in scores. Update the existing row instead of adding another.`);
}

async function p05Transfer(p: Practice) {
  const db = await freshDb(p);
  db.prepare("INSERT INTO scores (user_id, points) VALUES (?, ?), (?, ?)").run("a", 50, "b", 0);
  const points = (user: string) => (db.prepare("SELECT points FROM scores WHERE user_id = ?").get(user) as Any)?.points ?? 0;
  await returns(p, "transferPoints", [db, "a", "b", 20], true);
  if (points("a") !== 30 || points("b") !== 20) fail(`After moving 20 points from a (50) to b (0), a has ${points("a")} and b has ${points("b")}.`);
  await returns(p, "transferPoints", [db, "a", "b", 31], false);
  if (points("a") !== 30 || points("b") !== 20) fail("A transfer of more points than a has should change nothing.");
  await returns(p, "transferPoints", [db, "a", "newcomer", 5], true);
  if (points("newcomer") !== 5) fail("transferPoints() to a user with no row yet should give them the points.");
  if (db.isTransaction) fail("transferPoints() left a transaction open. COMMIT or ROLLBACK every time.");
}

async function p05FindUser(p: Practice) {
  const db = await freshDb(p);
  db.prepare("INSERT INTO users (id, name) VALUES (?, ?), (?, ?)").run("1", "Ana", "2", "O'Brien");
  await returns(p, "findUserId", [db, "Ana"], "1");
  await returns(p, "findUserId", [db, "O'Brien"], "2");
  await returns(p, "findUserId", [db, "x' OR '1'='1"], null);
}

// --- Module 06 ---------------------------------------------------------------
async function p06Ids(p: Practice) {
  for (const [pollId, index] of [["1300000000000000001", 0], ["42", 4]] as const) {
    const id = await p.call("encodeVote", pollId, index);
    if (id !== `vote:${pollId}:${index}`) fail(`encodeVote(${show(pollId)}, ${index}) returned ${show(id)}, but should return "vote:${pollId}:${index}".`);
    await returns(p, "decodeVote", [id], { pollId, index });
  }
  for (const id of ["hello", "", "vote:", "vote:42", "vote:42:x", "vote::1", "nope:42:1", "vote:42:-1", "vote:42:1:2", "vote:42:1.5"]) {
    await returns(p, "decodeVote", [id], null);
  }
}

async function p06ProgressBar(p: Practice) {
  await returns(p, "progressBar", [0.5], "#####-----");
  await returns(p, "progressBar", [0.25, 8], "##------");
  await returns(p, "progressBar", [0.66, 3], "##-");
  await returns(p, "progressBar", [1.5, 4], "####");
  await returns(p, "progressBar", [-1, 4], "----");
  await returns(p, "progressBar", [Number.NaN, 4], "----");
}

async function p06Tally(p: Practice) {
  const votes = new Map([["u1", 0], ["u2", 2], ["u3", 0], ["u4", 7]]);
  await returns(p, "tally", [votes, 3], [2, 0, 1]);
  await returns(p, "tally", [new Map(), 2], [0, 0]);
}

async function p06Winners(p: Practice) {
  await returns(p, "winners", [[3, 5, 1]], [1]);
  await returns(p, "winners", [[4, 1, 4]], [0, 2]);
  await returns(p, "winners", [[0, 0]], []);
  await returns(p, "winners", [[]], []);
}

// Each problem: a label and its test, in the order they appear in the file.
// "functions" lists which functions in the file belong to the problem, so
// type errors can be reported against the right one.
interface Problem {
  label: string;
  functions: string[];
  test: PracticeTest;
}

const PRACTICE: Record<number, Problem[]> = {
  1: [
    { label: "sleep()", functions: ["sleep"], test: p01Sleep },
    { label: "withTimeout()", functions: ["withTimeout"], test: p01WithTimeout },
    { label: "fetchAll()", functions: ["fetchAll"], test: p01FetchAll },
    { label: "totalLength() (fix the bug)", functions: ["totalLength"], test: p01TotalLength },
  ],
  2: [
    { label: "parseDuration()", functions: ["parseDuration"], test: p02ParseDuration },
    { label: "formatDuration()", functions: ["formatDuration"], test: p02FormatDuration },
    { label: "parseColor()", functions: ["parseColor"], test: p02ParseColor },
    { label: "totalSeconds() (fix the bug)", functions: ["totalSeconds"], test: p02TotalSeconds },
  ],
  3: [
    { label: "toReply()", functions: ["toReply"], test: p03ToReply },
    { label: "CooldownError", functions: ["CooldownError"], test: p03CooldownError },
    { label: "truncate()", functions: ["truncate"], test: p03Truncate },
    { label: "jsonError() (fix the bug)", functions: ["jsonError"], test: p03JsonError },
  ],
  4: [
    { label: "checkClamp()", functions: ["checkClamp"], test: p04CheckClamp },
    { label: "Cooldown", functions: ["Cooldown"], test: p04Cooldown },
    { label: "makeSequenceRng()", functions: ["makeSequenceRng"], test: p04SequenceRng },
    { label: "newSettings() (fix the bug)", functions: ["newSettings"], test: p04NewSettings },
  ],
  5: [
    { label: "addNote() and notesFor()", functions: ["addNote", "notesFor"], test: p05Notes },
    { label: "addPoints()", functions: ["addPoints"], test: p05AddPoints },
    { label: "transferPoints()", functions: ["transferPoints"], test: p05Transfer },
    { label: "findUserId() (fix the bug)", functions: ["findUserId"], test: p05FindUser },
  ],
  6: [
    { label: "encodeVote() and decodeVote()", functions: ["encodeVote", "decodeVote"], test: p06Ids },
    { label: "progressBar()", functions: ["progressBar"], test: p06ProgressBar },
    { label: "tally()", functions: ["tally"], test: p06Tally },
    { label: "winners() (fix the bug)", functions: ["winners"], test: p06Winners },
  ],
};

// (Runs in its own process.) Tests one problem and prints the result as JSON.
async function runOnePractice(module: number, index: number, file: string): Promise<void> {
  const problem = PRACTICE[module]![index]!;
  let status = "pass";
  let message = "";
  try {
    const mod = await withQuietConsole(() => import(pathToFileURL(file).href));
    await withQuietConsole(() => problem.test(new Practice(mod)));
  } catch (error) {
    if (error instanceof NotStarted) status = "todo";
    else if (error instanceof CheckFailed) [status, message] = ["fail", error.message];
    else [status, message] = ["fail", `Node couldn't load the file: ${(error as Error).message}`];
  }
  say("\n" + JSON.stringify({ status, message }));
  process.exit(0);
}

// Type-checks one practice file, and sorts the errors by the function (or
// class) they're in, using where each "export" starts.
function practiceTypeErrors(file: string): Map<string, string[]> {
  const result = run([tscPath(), "--noEmit", "--strict", "--target", "es2022", "--module", "nodenext",
    "--moduleResolution", "nodenext", "--allowImportingTsExtensions", "--erasableSyntaxOnly",
    "--verbatimModuleSyntax", "--skipLibCheck", "--types", "node", "--ignoreConfig", file]);
  const byName = new Map<string, string[]>();
  if (result.code === 0) return byName;
  const lines = readText(file).split(/\r?\n/);
  const starts: [number, string][] = [];
  lines.forEach((line, i) => {
    const match = /^export\s+(?:async\s+)?(?:function|class)\s+(\w+)/.exec(line);
    if (match) starts.push([i + 1, match[1]!]);
  });
  for (const line of result.output.split("\n")) {
    const match = /\((\d+),\d+\): error (TS\d+: .*)$/.exec(line);
    if (!match) continue;
    const at = Number(match[1]);
    const owner = [...starts].reverse().find(([start]) => start <= at)?.[1] ?? "*";
    byName.set(owner, [...(byName.get(owner) ?? []), `line ${at}: ${match[2]}`]);
  }
  return byName;
}

function runPractice(module: number, file: string): void {
  const problems = PRACTICE[module]!;
  const typeErrors = practiceTypeErrors(file);
  let solved = 0;
  problems.forEach((problem, index) => {
    const label = `${index + 1}. ${problem.label}`;
    const result = spawnSync(process.execPath, ["--no-warnings", THIS_FILE, "--practice-one", String(module), String(index), file], {
      encoding: "utf8", timeout: PRACTICE_TIMEOUT, cwd: ROOT,
    });
    let outcome = { status: "fail", message: "" };
    if (result.error && (result.error as NodeJS.ErrnoException).code === "ETIMEDOUT") {
      outcome.message = `Still running after ${PRACTICE_TIMEOUT / 1000} seconds. Is there a loop that never ends, or a promise that never settles?`;
    } else {
      try {
        outcome = JSON.parse(result.stdout.trim().split("\n").pop() ?? "");
      } catch {
        // Node exits with code 13 when it's left waiting on a promise that
        // nothing will ever resolve.
        outcome.message = result.status === 13
          ? "It never finished: it's waiting on a promise that never resolves or rejects."
          : firstLines(result.stderr.trim() || `It stopped early (exit code ${result.status}).`, 6);
      }
    }
    const errors = [...problem.functions.flatMap((name) => typeErrors.get(name) ?? []), ...(typeErrors.get("*") ?? [])];
    if (outcome.status !== "todo" && errors.length > 0) {
      outcome = { status: "fail", message: `TypeScript found a problem: ${errors[0]}${errors.length > 1 ? ` (and ${errors.length - 1} more)` : ""}` };
    }
    if (outcome.status === "pass") {
      solved++;
      say(`[PASS]    ${label}`);
    } else if (outcome.status === "todo") {
      say(`[TODO]    ${label}  (not started yet)`);
    } else {
      say(`[NOT YET] ${label}\n          ${outcome.message.split("\n").join("\n          ")}`);
    }
  });
  say(`\n${solved} of ${problems.length} practice problems solved.`);
  if (solved === problems.length) say("All done. On to the steps!");
  process.exit(solved === problems.length ? 0 : 1);
}

// ---------------------------------------------------------------------------
// Running the checks
// ---------------------------------------------------------------------------

// (Runs in its own process, in an empty temporary folder, so anything your
// bot creates there, like a database, doesn't end up in your project.)
async function runChecks(module: number): Promise<void> {
  for (let number = 0; number <= module; number++) {
    say(`Module ${String(number).padStart(2, "0")}:`);
    try {
      await CHECKS[number]!();
    } catch (error) {
      if (error instanceof CheckFailed) {
        say(`\n[NOT YET] ${error.message}`);
        process.exit(1);
      }
      say(`\n[NOT YET] Something unexpected went wrong while checking:\n${firstLines((error as Error).stack ?? String(error), 10)}`);
      process.exit(1);
    }
  }
  say(`\n[PASS] Everything up to module ${String(module).padStart(2, "0")} works. Nice!`);
  process.exit(0);
}

const USAGE = `Usage:
    node check.ts N             check modules 0 to N (N is 0 to ${CHECKS.length - 1})
    node check.ts practice N    test practice_0N.ts (N is 1 to 6)`;

async function main(): Promise<void> {
  const args = process.argv.slice(2);

  // Used internally: run the module checks in a separate process.
  if (args[0] === "--run") {
    ROOT = args[2]!;
    await runChecks(Number(args[1]));
    return;
  }
  if (args[0] === "--practice-one") {
    await runOnePractice(Number(args[1]), Number(args[2]), args[3]!);
    return;
  }

  if (args[0] === "practice") {
    const module = Number(args[1]);
    if (!PRACTICE[module]) {
      say(USAGE);
      process.exit(1);
    }
    const file = resolve(args[2] ?? `practice_${String(module).padStart(2, "0")}.ts`);
    if (!existsSync(file)) {
      say(`Couldn't find ${file}.`);
      say(`Copy practice_${String(module).padStart(2, "0")}.ts from the module's folder into this folder first.`);
      process.exit(1);
    }
    runPractice(module, file);
    return;
  }

  const module = Number(args[0]);
  if (!/^\d+$/.test(args[0] ?? "") || module >= CHECKS.length) {
    say(USAGE);
    process.exit(1);
  }
  if (!existsSync(path("package.json"))) {
    say("Couldn't find package.json here. Run this from your bot's folder (where package.json is).");
    process.exit(1);
  }
  const scratch = mkdtempSync(join(tmpdir(), "bot-check-"));
  const result = spawnSync(process.execPath, ["--no-warnings", THIS_FILE, "--run", String(module), ROOT], {
    cwd: scratch, stdio: "inherit", timeout: CHECK_TIMEOUT, env: { ...process.env, DISCORD_TOKEN: "" },
  });
  rmSync(scratch, { recursive: true, force: true });
  if (result.error && (result.error as NodeJS.ErrnoException).code === "ETIMEDOUT") {
    say(`\n[NOT YET] The check was still running after ${CHECK_TIMEOUT / 1000} seconds. Is something in your bot waiting forever?`);
    process.exit(1);
  }
  process.exit(result.status ?? 1);
}

await main();
