import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import Body from "https://esm.sh/react-muscle-highlighter@1.2.0?external=react,react-dom,react/jsx-runtime";

const rootEl = document.getElementById("muscle-react-root");

if (rootEl) {
  const gender = rootEl.dataset.sex === "female" ? "female" : "male";

  const fullBodySlugs = [
    "abs", "adductors", "ankles", "biceps", "calves", "chest", "deltoids", "feet",
    "forearm", "gluteal", "hamstring", "hands", "head", "knees", "lower-back", "neck",
    "obliques", "quadriceps", "tibialis", "trapezius", "triceps", "upper-back",
  ];

  const zoneToSlugs = {
    chest: ["chest"],
    back: ["upper-back", "lower-back", "trapezius"],
    shoulders: ["deltoids", "trapezius"],
    arms: ["biceps", "triceps", "forearm"],
    core: ["abs", "obliques"],
    glutes: ["gluteal"],
    quads: ["quadriceps", "tibialis"],
    hamstrings: ["hamstring"],
    calves: ["calves"],
    full_body: fullBodySlugs,
  };

  function toBodyData(zones) {
    const normalized = Array.isArray(zones) ? zones : [];
    const slugs = new Set();

    normalized.forEach((zone) => {
      const mapped = zoneToSlugs[zone];
      if (!mapped) return;
      mapped.forEach((slug) => slugs.add(slug));
    });

    if (slugs.size === 0) {
      return [];
    }

    return Array.from(slugs).map((slug) => ({
      slug,
      color: "#ff8e5b",
      intensity: 1,
    }));
  }

  function MuscleMapApp() {
    const [zones, setZones] = useState([]);

    useEffect(() => {
      const handler = (event) => {
        setZones(event?.detail?.zones || []);
      };

      document.addEventListener("myfit:exercise-zones-changed", handler);
      return () => {
        document.removeEventListener("myfit:exercise-zones-changed", handler);
      };
    }, []);

    const bodyData = useMemo(() => toBodyData(zones), [zones]);

    return React.createElement(
      "div",
      { className: "body-map-react-grid" },
      React.createElement(
        "div",
        { className: "body-card" },
        React.createElement("h4", null, "Fronte"),
        React.createElement(Body, {
          data: bodyData,
          side: "front",
          gender,
          scale: 1.2,
          border: "#d8e1de",
          defaultFill: "#d7dfdc",
          defaultStroke: "#8da39c",
          defaultStrokeWidth: 0.8,
        })
      ),
      React.createElement(
        "div",
        { className: "body-card" },
        React.createElement("h4", null, "Retro"),
        React.createElement(Body, {
          data: bodyData,
          side: "back",
          gender,
          scale: 1.2,
          border: "#d8e1de",
          defaultFill: "#d7dfdc",
          defaultStroke: "#8da39c",
          defaultStrokeWidth: 0.8,
        })
      )
    );
  }

  createRoot(rootEl).render(React.createElement(MuscleMapApp));
}
