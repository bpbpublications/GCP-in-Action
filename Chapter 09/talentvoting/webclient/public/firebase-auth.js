function initFirebaseAuth(config) {
  if (!config.projectId) throw Error('Missing projectId');
  if (!config.apiKey) throw Error('Missing apiKey');
  if (!config.authDomain) throw Error('Missing authDomain');

  const firebaseConfig = {
    apiKey: config.apiKey,
    projectId: config.projectId,
    authDomain: config.authDomain
  }
  firebase.initializeApp(firebaseConfig);

  firebase.auth().onAuthStateChanged(async function(user) {
    if (!user && config.loggedOut) {
      config.loggedOut();
      return;
    }
    if (!config.loggedIn) return;
    const token = await user.getIdToken();
    config.loggedIn(user, token);
  });
}

function logout() {
  firebase.auth().signOut();
}

function handleAuthError(error, onError) {
  if (error.code === "auth/unauthorized-domain") {
      const authDomain = firebase.auth().app.options.authDomain;
      const projectName = authDomain.replace('.firebaseapp.com', '');
      onError(new Error(`Looks like your domain isn't valid for this project. Please check your Firebase Auth domain configuration. https://console.firebase.google.com/u/0/project/${projectName}/authentication/providers`));
  } else {
    onError(error)
  }
}

function googleLogin(onError) {
  var provider = new firebase.auth.GoogleAuthProvider();
  firebase.auth().signInWithPopup(provider).then(() => {}, (error) => handleAuthError(error, onError));
}

export {
  initFirebaseAuth,
  googleLogin,
  logout
}