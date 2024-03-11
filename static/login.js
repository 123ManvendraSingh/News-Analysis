import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-app.js";
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js";

// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
    apiKey: "AIzaSyD7Jo99-wZH8Ae23toSzJp0B3g8xB1RAMw",
    authDomain: "news-566c2.firebaseapp.com",
    projectId: "news-566c2",
    storageBucket: "news-566c2.appspot.com",
    messagingSenderId: "164891454040",
    appId: "1:164891454040:web:29a48ad162f9f3ff24782d",
    measurementId: "G-1SJKM2WE7P"
  };

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

const googleSignInBtn = document.getElementById('l');

const provider = new GoogleAuthProvider();
console.log("I wasa executed! before auth")
googleSignInBtn.addEventListener('click', () => {
  console.log("I wasa executed! before auth")
  signInWithPopup(auth, provider)
    .then((result) => {
      const user = result.user;
      location.replace('/process')
});
});