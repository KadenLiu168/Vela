import { useEffect, useState } from "react";
import { ApiClientError, getHealth } from "../api/client";

export function HomePage() {
  const [apiStatus, setApiStatus] = useState("checking");

  useEffect(() => {
    let isCurrent = true;

    getHealth()
      .then((health) => {
        if (isCurrent) {
          setApiStatus(health.status);
        }
      })
      .catch((error: unknown) => {
        if (isCurrent) {
          setApiStatus(error instanceof ApiClientError ? error.kind : "unavailable");
        }
      });

    return () => {
      isCurrent = false;
    };
  }, []);

  return (
    <section className="home-page">
      <p>Frontend skeleton ready</p>
      <p>API status: {apiStatus}</p>
    </section>
  );
}
