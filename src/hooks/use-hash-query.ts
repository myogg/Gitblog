import { useState, useEffect } from "react";

export function useHashQuery() {
  const getSearchParams = () => {
    const hash = window.location.hash;
    const queryString = hash.includes("?") ? hash.split("?")[1] : "";
    return new URLSearchParams(queryString);
  };

  const [searchParams, setSearchParams] = useState(getSearchParams());

  useEffect(() => {
    const onChange = () => {
      setSearchParams(getSearchParams());
    };

    window.addEventListener("hashchange", onChange);
    // Also listen to popstate for history navigation
    window.addEventListener("popstate", onChange);
    
    return () => {
      window.removeEventListener("hashchange", onChange);
      window.removeEventListener("popstate", onChange);
    };
  }, []);

  return searchParams;
}
