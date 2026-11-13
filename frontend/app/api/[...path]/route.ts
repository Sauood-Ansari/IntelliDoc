import { NextRequest, NextResponse } from "next/server";
export const runtime = "nodejs";
const API = process.env.BACKEND_URL || "http://127.0.0.1:8000";
async function handler(req: NextRequest, context: {params: Promise<{path:string[]}>}) {
  const {path} = await context.params;
  if(path.some(p => !/^[a-zA-Z0-9_-]+$/.test(p))) return NextResponse.json({detail:"Invalid path"},{status:400});
  if (!["GET", "HEAD"].includes(req.method)) {
    const origin = req.headers.get("origin");
    let sameHost = false;
    try { sameHost = !!origin && new URL(origin).host === req.headers.get("host"); } catch {}
    if (origin && !sameHost && origin !== req.nextUrl.origin && origin !== process.env.APP_ORIGIN)
      return NextResponse.json({detail:"Request origin not allowed"},{status:403});
  }
  if(path.join("/") === "auth/logout") {
    const response = NextResponse.json({ok:true});
    response.cookies.delete("intellidoc_session");
    return response;
  }
  const headers = new Headers();
  const token = req.cookies.get("intellidoc_session")?.value;
  if(token) headers.set("Authorization", "Bearer " + token);
  const contentType = req.headers.get("content-type");
  if(contentType) headers.set("Content-Type",contentType);
  let body: Uint8Array | undefined;
  if(!["GET","HEAD"].includes(req.method)) {
    const reader = req.body?.getReader();
    const chunks: Uint8Array[] = [];
    let size = 0;
    if(reader) while(true) {
      const {done,value} = await reader.read();
      if(done) break;
      size += value.length;
      if(size > 11 * 1024 * 1024) {
        await reader.cancel();
        return NextResponse.json({detail:"Upload exceeds 10 MB"},{status:413});
      }
      chunks.push(value);
    }
    body = new Uint8Array(size);
    let offset = 0;
    for(const chunk of chunks) {body.set(chunk,offset); offset += chunk.length;}
  }
  try {
    const upstream = await fetch(API + "/api/v1/" + path.join("/") + req.nextUrl.search,
      {method:req.method,headers,body:body as BodyInit | undefined,cache:"no-store",signal:AbortSignal.timeout(120000)});
    const data = await upstream.json();
    if(path.join("/") === "auth/login" && upstream.ok) {
      const {access_token,...profile} = data;
      const response = NextResponse.json(profile);
      response.cookies.set("intellidoc_session",access_token,{httpOnly:true,sameSite:"lax",
        secure:process.env.COOKIE_SECURE === "true",path:"/",maxAge:3600});
      return response;
    }
    const response = NextResponse.json(data,{status:upstream.status});
    if(upstream.status === 401) response.cookies.delete("intellidoc_session");
    return response;
  } catch {
    return NextResponse.json({detail:"The backend is unavailable. Start the API service and try again."},{status:503});
  }
}
export {handler as GET, handler as POST, handler as PATCH, handler as DELETE};

