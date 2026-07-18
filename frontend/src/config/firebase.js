const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID,
}

export const firebaseConfigured = [
  firebaseConfig.apiKey,
  firebaseConfig.authDomain,
  firebaseConfig.projectId,
  firebaseConfig.appId,
].every(Boolean)

let authContextPromise

export async function getFirebaseAuthContext() {
  if (!firebaseConfigured) return null
  if (!authContextPromise) {
    authContextPromise = Promise.all([
      import('firebase/app'),
      import('firebase/auth'),
    ]).then(([appModule, authModule]) => {
      const app = appModule.initializeApp(firebaseConfig)
      const auth = authModule.getAuth(app)
      const googleProvider = new authModule.GoogleAuthProvider()
      googleProvider.setCustomParameters({ prompt: 'select_account' })
      return {
        auth,
        googleProvider,
        signInWithPopup: authModule.signInWithPopup,
      }
    })
  }
  return authContextPromise
}
