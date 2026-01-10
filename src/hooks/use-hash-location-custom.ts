import { useState, useEffect, useCallback } from "react";
import { BaseLocationHook } from "wouter/use-location";

// Helper to get current location from hash, stripping query params
const currentLoc = () => {
  // Get hash content, remove leading #
  const hash = window.location.hash.replace(/^#/, "") || "/";
  // Strip query string (everything after ?) for path matching
  // So /?page=2 becomes /
  return hash.split("?")[0];
};

export const useHashLocation: BaseLocationHook = () => {
  const [loc, setLoc] = useState(currentLoc());

  useEffect(() => {
    const handler = () => setLoc(currentLoc());

    // Subscribe to hash changes
    window.addEventListener("hashchange", handler);
    // Also listen to popstate for history navigation
    window.addEventListener("popstate", handler);
    
    return () => {
      window.removeEventListener("hashchange", handler);
      window.removeEventListener("popstate", handler);
    };
  }, []);

  const navigate = useCallback((to: string) => {
    window.location.hash = to;
  }, []);

  return [loc, navigate];
};
