import { auth } from "@/lib/auth";
import { NextResponse } from "next/server";
import { hasDevAccess } from "@/lib/roles";

export default auth((req) => {
  const { nextUrl, auth: session } = req;
  const isLoggedIn = !!session;
  const pathname = nextUrl.pathname;

  // Routes publiques : toujours accessibles
  const publicRoutes = ["/", "/login", "/pricing", "/api/auth"];
  const isPublic = publicRoutes.some((route) => pathname.startsWith(route));

  if (isPublic) return NextResponse.next();

  // Routes dashboard : nécessitent d'être connecté
  if (pathname.startsWith("/dashboard")) {
    if (!isLoggedIn) {
      return NextResponse.redirect(new URL("/login", req.url));
    }
    return NextResponse.next();
  }

  // Routes /dev : nécessitent un rôle >= SUPPORT
  if (pathname.startsWith("/dev")) {
    if (!isLoggedIn) {
      return NextResponse.redirect(new URL("/login", req.url));
    }
    const userRoles = session.user?.roles ?? ["USER"];
    if (!hasDevAccess(userRoles)) {
      return NextResponse.redirect(new URL("/dashboard", req.url));
    }
    return NextResponse.next();
  }

  // Routes API : protégées individuellement dans chaque route handler
  if (pathname.startsWith("/api")) {
    return NextResponse.next();
  }

  return NextResponse.next();
});

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
