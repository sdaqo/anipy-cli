import { webcrack } from 'webcrack';
import fs from 'fs';

function transform(n, t) {
        var s = [], j = 0, x, res = '';
        for (var i = 0; i < 256; i++) {
                s[i] = i;
        }
        for (i = 0; i < 256; i++) {
                j = (j + s[i] + n.charCodeAt(i % n.length)) % 256;
                x = s[i];
                s[i] = s[j];
                s[j] = x;
        }
        i = 0;
        j = 0;
        for (var y = 0; y < t.length; y++) {
                i = (i + 1) % 256;
                j = (j + s[i]) % 256;
                x = s[i];
                s[i] = s[j];
                s[j] = x;
                res += String.fromCharCode(t.charCodeAt(y) ^ s[(s[i] + s[j]) % 256]);
        }
        return res;
}

function substitute(n, t, i) {
        for (var r = t.length, u = {}; r-- && (u[t[r]] = i[r] || ""););
        return n.split("").map(function(n) {
                return u[n] || n;
        }).join("");
}


function base64_url_encode(n) {
        return (n = (n = btoa(n)).replace(/\+/g, "-").replace(/\//g, "_")).replace(/=+$/, "");
}
function base64_url_decode(n) {
        var t = n;
        n = 4 - n.length % 4;
        if (n < 4) {
                t += "=".repeat(n);
        }
        t = t.replace(/-/g, "+").replace(/_/g, "/");
        return atob(t);
}

function reverse_it(n) {
        return n.split("").reverse().join("");
}

function find_all_functions(jsCode, functionPattern) {
        const matches = [];
        const regex = new RegExp(functionPattern, "g");

        let match;
        while ((match = regex.exec(jsCode)) !== null) {
                let startIdx = match.index;
                let bracketCount = 0;
                let endIdx = startIdx;

                while (jsCode[endIdx] !== "{" && endIdx < jsCode.length) {
                        endIdx++;
                }

                if (jsCode[endIdx] === "{") bracketCount++;
                while (bracketCount > 0 && endIdx < jsCode.length) {
                        endIdx++;
                        if (jsCode[endIdx] === "{") bracketCount++;
                        if (jsCode[endIdx] === "}") bracketCount--;
                }

                matches.push(jsCode.slice(startIdx, endIdx + 1));
        }
        return matches.length ? matches : null;
}

async function animekai_home() {
        const url = 'https://animekai.to/home';
        const res = await fetch(url);
        const html = await res.text();
        const bundle_url = html.match(/https:\/\/[^"]*bundle\.js[^"]*/);
        const ani_id = []
        html.match(/data\-id\=\"([a-zA-Z0-9\-_]+)\"/g).forEach((i) => {
                let id = i.split('"')[1].split('"')[0];
                ani_id.push(id);
        });
        return { "bundle": bundle_url[0], ani_id: ani_id }
}

function get_name(func) {
        return func.split(" ")[1].split("(")[0];
}

async function episode(ani_id, encode_func) {
        function evaluate(n) {
                return eval(encode_func);
        }
        for (let i = 0; i < ani_id.length; i++) {
                const url = new URL('https://animekai.to/ajax/episodes/list');
                url.searchParams.append('ani_id', ani_id[i]);
                url.searchParams.append('_', evaluate(ani_id[i]));
                const res = await fetch(url);
                const data = await res.json();
                const token = data["result"].match(/token\=\"([a-zA-Z0-9\-_]+)\"/g);
                if (token !== null) {
                        return token[0].split('"')[1].split('"')[0];
                }
        }
}

async function mega_url(token, encode_func, decode_func) {
        function enc_evaluate(n) {
                return eval(encode_func);
        }
        function dec_evaluate(n) {
                return eval(decode_func);
        }
        let url = new URL('https://animekai.to/ajax/links/list');
        url.searchParams.append('token', token);
        url.searchParams.append('_', enc_evaluate(token));
        let res = await fetch(url);
        let data = await res.json();
        const episodeServer = data["result"].match(/data\-lid=\"([a-zA-Z0-9\-_]+)\"/g)[0].split('"')[1].split('"')[0];
        url = new URL('https://animekai.to/ajax/links/view');
        url.searchParams.append('id', episodeServer);
        url.searchParams.append('_', enc_evaluate(episodeServer));
        res = await fetch(url);
        data = await res.json();
        return JSON.parse(decodeURIComponent(dec_evaluate(data["result"])))["url"];
}

async function mega_js(mega_url) {
        const res = await fetch(mega_url);
        const html = await res.text();
        const app_url = html.match(/src=["']([^"']*app\.js[^"']*)["']/);
        return `https://megaup.cc/${app_url[1].trim()}`;
}

async function deobfuscate(url, func1, func2) {
        let res = await fetch(url);
        const data = await res.text();
        const result = await webcrack(data);
        const btoaPos = result.code.indexOf("btoa(");
        const btoaBefore = result.code.slice(0, btoaPos);
        const lastFuncPos = btoaBefore.lastIndexOf("[function");
        const lastFuncAfter = result.code.indexOf("{", lastFuncPos);
        const function_name = result.code.slice(lastFuncPos - 5, lastFuncAfter + 1);
        const main_function_start = result.code.split(function_name)[1];
        const main_function_end = main_function_start.split("}]")[0];
        const extractedFunctions = find_all_functions(main_function_end, /function\s+\w\(\s*\w+(\s*,\s*\w+)*\s*\)\s*\{/g);
        const map = new Map();
        let decodeFunc;
        let encodeFunc;
        for (let i = 0; i < extractedFunctions.length; i++) {
                if (extractedFunctions[i].includes("256")) {
                        map.set(get_name(extractedFunctions[i]), "transform");
                } else if (extractedFunctions[i].includes("btoa")) {
                        map.set(get_name(extractedFunctions[i]), "base64_url_encode");
                } else if (extractedFunctions[i].includes("atob")) {
                        map.set(get_name(extractedFunctions[i]), "base64_url_decode");
                } else if (extractedFunctions[i].includes("return n =") || extractedFunctions[i].includes("encodeURIComponent")) {
                        if (extractedFunctions[i].includes("encodeURIComponent")) {
                                encodeFunc = extractedFunctions[i].replace('n = encodeURIComponent(n)', 'n').split("return n = ")[1].split(";")[0].trim();
                        } else {
                                encodeFunc = extractedFunctions[i].split("return n = ")[1].split(";")[0].trim();
                        }
                } else if (extractedFunctions[i].includes(".reverse")) {
                        map.set(get_name(extractedFunctions[i]), "reverse_it");
                } else if (extractedFunctions[i].includes(".map")) {
                        map.set(get_name(extractedFunctions[i]), "substitute");
                } else if (extractedFunctions[i].includes("n = `${n}`;") || extractedFunctions[i].includes("decodeURIComponent")) {
                        if (extractedFunctions[i].includes("decodeURIComponent")) {
                                decodeFunc = extractedFunctions[i].replace('n = `${n}`', 'n').split("n =")[1].split(";")[0].trim();
                        } else {
                                decodeFunc = extractedFunctions[i].split("n = `${n}`")[1].split("n =")[1].split(";")[0].trim();
                        }
                }
        }
        const matchHt = main_function_end.match(/var\s+(\w+)\s*=\s*\w+\.Ht\s*;/);
        if (matchHt !== null) {
                map.set(matchHt[0].split("=")[0].trim().split(" ")[1], "reverse_it");
        }
        
        const matchDollarT = main_function_end.match(/var\s+(\w+)\s*=\s*\w+\.\$t\s*;/);
        if (matchDollarT !== null) {
                map.set(matchDollarT[0].split("=")[0].trim().split(" ")[1], "substitute");
        }

        for (let [key, value] of map) {
                const regex = new RegExp(`\\b${key}\\b`, 'g');
                decodeFunc = decodeFunc.replace(regex, value);
        }

        for (let [key, value] of map) {
                const regex = new RegExp(`\\b${key}\\b`, 'g');
                encodeFunc = encodeFunc.replace(regex, value);
        }
        return { [func1]: encodeFunc, [func2]: decodeFunc }
}

const home = await animekai_home();
const result = await deobfuscate(home["bundle"], "generate_token", "decode_iframe_data");
const token = await episode(home["ani_id"], result["generate_token"]);
const mega_json_url = await mega_js(await mega_url(token, result["generate_token"], result["decode_iframe_data"]));
const result2 = await deobfuscate(mega_json_url, "encode", "decode");
const final = JSON.stringify({ ...result, ...result2 });
fs.writeFileSync("./generated/kai.json",final);
