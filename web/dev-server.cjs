const http = require("http");
const fs = require("fs");
const path = require("path");

const host = process.env.HOST || "127.0.0.1";
const port = Number(process.env.PORT || 5173);
const root = process.cwd();

const mimeByExt = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".txt": "text/plain; charset=utf-8"
};

function resolvePath(urlPath) {
  let safePath = decodeURIComponent((urlPath || "/").split("?")[0].split("#")[0]);
  if (safePath === "/") safePath = "/index.html";
  if (safePath.endsWith("/")) safePath += "index.html";
  if (!path.extname(safePath)) safePath += ".html";

  const candidate = path.normalize(path.join(root, safePath));
  if (!candidate.startsWith(root)) return null;
  return candidate;
}

const server = http.createServer((req, res) => {
  const target = resolvePath(req.url);
  if (!target) {
    res.writeHead(400, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("Bad request");
    return;
  }

  fs.readFile(target, (err, data) => {
    if (err) {
      if (err.code === "ENOENT") {
        res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
        res.end("Not found");
        return;
      }
      res.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
      res.end("Internal server error");
      return;
    }

    const ext = path.extname(target).toLowerCase();
    const contentType = mimeByExt[ext] || "application/octet-stream";
    res.writeHead(200, { "Content-Type": contentType });
    res.end(data);
  });
});

server.listen(port, host, () => {
  console.log(`Dev server running at http://${host}:${port}`);
});
