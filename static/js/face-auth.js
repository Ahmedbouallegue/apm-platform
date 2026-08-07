/**
 * Topnet APM — facial enroll / login (face-api.js).
 * Expects data attributes on #face-auth-root or per-mode containers.
 */
(function () {
  "use strict";

  var FACE_API_SRC =
    "https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/dist/face-api.min.js";
  var MODELS_URL =
    "https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js@0.22.2/weights";

  var modelsReady = null;
  var activeStream = null;

  function getCookie(name) {
    var match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
    return match ? decodeURIComponent(match[2]) : "";
  }

  function setStatus(el, message, kind) {
    if (!el) return;
    el.textContent = message || "";
    el.className = "face-status" + (kind ? " is-" + kind : "");
  }

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      if (window.faceapi) {
        resolve();
        return;
      }
      var existing = document.querySelector('script[data-face-api="1"]');
      if (existing) {
        existing.addEventListener("load", resolve);
        existing.addEventListener("error", reject);
        return;
      }
      var script = document.createElement("script");
      script.src = src;
      script.async = true;
      script.dataset.faceApi = "1";
      script.onload = resolve;
      script.onerror = function () {
        reject(new Error("Impossible de charger face-api.js"));
      };
      document.head.appendChild(script);
    });
  }

  function ensureModels() {
    if (modelsReady) return modelsReady;
    modelsReady = loadScript(FACE_API_SRC).then(function () {
      return Promise.all([
        faceapi.nets.tinyFaceDetector.loadFromUri(MODELS_URL),
        faceapi.nets.faceLandmark68Net.loadFromUri(MODELS_URL),
        faceapi.nets.faceRecognitionNet.loadFromUri(MODELS_URL),
      ]);
    });
    return modelsReady;
  }

  function stopStream() {
    if (!activeStream) return;
    activeStream.getTracks().forEach(function (track) {
      track.stop();
    });
    activeStream = null;
  }

  function startCamera(video) {
    stopStream();
    return navigator.mediaDevices
      .getUserMedia({
        video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      })
      .then(function (stream) {
        activeStream = stream;
        video.srcObject = stream;
        return video.play();
      });
  }

  function extractDescriptor(video) {
    var options = new faceapi.TinyFaceDetectorOptions({
      inputSize: 320,
      scoreThreshold: 0.5,
    });
    return faceapi
      .detectSingleFace(video, options)
      .withFaceLandmarks()
      .withFaceDescriptor()
      .then(function (detection) {
        if (!detection || !detection.descriptor) {
          throw new Error("Aucun visage détecté. Placez-vous face à la caméra.");
        }
        return Array.from(detection.descriptor);
      });
  }

  function postJson(url, body) {
    return fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify(body),
    }).then(function (response) {
      return response.json().then(function (data) {
        return { status: response.status, data: data };
      });
    });
  }

  function bindEnroll(root) {
    var video = root.querySelector("[data-face-video]");
    var status = root.querySelector("[data-face-status]");
    var startBtn = root.querySelector("[data-face-start]");
    var enrollBtn = root.querySelector("[data-face-enroll]");
    var clearBtn = root.querySelector("[data-face-clear]");
    var badge = root.querySelector("[data-face-badge]");
    var enrollUrl = root.dataset.enrollUrl;
    var clearUrl = root.dataset.clearUrl;

    if (startBtn) {
      startBtn.addEventListener("click", function () {
        setStatus(status, "Chargement des modèles…", "info");
        ensureModels()
          .then(function () {
            setStatus(status, "Activation de la caméra…", "info");
            return startCamera(video);
          })
          .then(function () {
            setStatus(status, "Caméra prête. Cadrez votre visage puis cliquez sur Enroler.", "ok");
            if (enrollBtn) enrollBtn.disabled = false;
          })
          .catch(function (err) {
            setStatus(
              status,
              err.message || "Caméra inaccessible. Autorisez l’accès dans le navigateur.",
              "error"
            );
          });
      });
    }

    if (enrollBtn) {
      enrollBtn.addEventListener("click", function () {
        enrollBtn.disabled = true;
        setStatus(status, "Analyse du visage…", "info");
        ensureModels()
          .then(function () {
            return extractDescriptor(video);
          })
          .then(function (descriptor) {
            setStatus(status, "Enregistrement…", "info");
            return postJson(enrollUrl, { descriptor: descriptor });
          })
          .then(function (result) {
            if (!result.data.ok) {
              throw new Error(result.data.error || "Échec de l’enrôlement.");
            }
            setStatus(status, result.data.message || "Visage enregistré.", "ok");
            if (badge) {
              badge.textContent = "Enrôlé";
              badge.className = "face-badge is-on";
            }
            if (clearBtn) clearBtn.hidden = false;
            stopStream();
          })
          .catch(function (err) {
            setStatus(status, err.message || "Erreur d’enrôlement.", "error");
          })
          .finally(function () {
            enrollBtn.disabled = false;
          });
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener("click", function () {
        if (!window.confirm("Retirer l’identifiant facial de ce compte ?")) return;
        setStatus(status, "Suppression…", "info");
        postJson(clearUrl, {})
          .then(function (result) {
            if (!result.data.ok) {
              throw new Error(result.data.error || "Échec de la suppression.");
            }
            setStatus(status, result.data.message || "Identifiant facial retiré.", "ok");
            if (badge) {
              badge.textContent = "Non enrôlé";
              badge.className = "face-badge";
            }
            clearBtn.hidden = true;
            stopStream();
          })
          .catch(function (err) {
            setStatus(status, err.message || "Erreur.", "error");
          });
      });
    }
  }

  function bindLogin(root) {
    var video = root.querySelector("[data-face-video]");
    var status = root.querySelector("[data-face-status]");
    var startBtn = root.querySelector("[data-face-start]");
    var loginBtn = root.querySelector("[data-face-login]");
    var loginUrl = root.dataset.loginUrl;

    if (startBtn) {
      startBtn.addEventListener("click", function () {
        setStatus(status, "Chargement des modèles…", "info");
        ensureModels()
          .then(function () {
            return startCamera(video);
          })
          .then(function () {
            setStatus(status, "Caméra prête. Cliquez sur Se connecter avec le visage.", "ok");
            if (loginBtn) loginBtn.disabled = false;
          })
          .catch(function (err) {
            setStatus(
              status,
              err.message || "Caméra inaccessible. Autorisez l’accès dans le navigateur.",
              "error"
            );
          });
      });
    }

    if (loginBtn) {
      loginBtn.addEventListener("click", function () {
        loginBtn.disabled = true;
        setStatus(status, "Vérification…", "info");
        ensureModels()
          .then(function () {
            return extractDescriptor(video);
          })
          .then(function (descriptor) {
            return postJson(loginUrl, { descriptor: descriptor });
          })
          .then(function (result) {
            if (!result.data.ok) {
              throw new Error(result.data.error || "Visage non reconnu.");
            }
            setStatus(status, "Connexion réussie…", "ok");
            stopStream();
            window.location.href = result.data.redirect || "/";
          })
          .catch(function (err) {
            setStatus(status, err.message || "Échec de la connexion faciale.", "error");
            loginBtn.disabled = false;
          });
      });
    }
  }

  function bindTabs(panel) {
    var tabs = panel.querySelectorAll("[data-auth-tab]");
    var panes = panel.querySelectorAll("[data-auth-pane]");
    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        var target = tab.getAttribute("data-auth-tab");
        tabs.forEach(function (t) {
          t.classList.toggle("is-active", t === tab);
        });
        panes.forEach(function (pane) {
          var on = pane.getAttribute("data-auth-pane") === target;
          pane.hidden = !on;
          pane.classList.toggle("is-active", on);
        });
        if (target !== "face") stopStream();
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-face-mode='enroll']").forEach(bindEnroll);
    document.querySelectorAll("[data-face-mode='login']").forEach(bindLogin);
    document.querySelectorAll("[data-auth-tabs]").forEach(bindTabs);
  });

  window.addEventListener("beforeunload", stopStream);
})();
