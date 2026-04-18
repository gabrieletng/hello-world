// Firebase initialization and functions for auth + Firestore

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
import { getAuth, signInWithPopup, GoogleAuthProvider, signOut, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";
import { getFirestore, collection, addDoc, query, where, getDocs, deleteDoc, doc, orderBy, getDoc } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js";

const firebaseConfig = {
  apiKey: "AIzaSyAnKRU_dd9Nwi_iDDo8gPOsfhzSy5Fty6E",
  authDomain: "loveanddeath-app.firebaseapp.com",
  projectId: "loveanddeath-app",
  storageBucket: "loveanddeath-app.firebasestorage.app",
  messagingSenderId: "944257976413",
  appId: "1:944257976413:web:fa3c7e5ba5e2f6899ea5b4",
  measurementId: "G-HBY4VKHE5Y"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);
const googleProvider = new GoogleAuthProvider();

// Configure Google provider to always show account selection
googleProvider.setCustomParameters({
  prompt: 'select_account'
});

// State
let currentUser = null;

// Authentication functions
export async function signInGoogle() {
  try {
    const result = await signInWithPopup(auth, googleProvider);
    currentUser = result.user;
    return result.user;
  } catch (error) {
    console.error("Sign-in error:", error.code, error.message);
    throw error;
  }
}

export async function signOutUser() {
  try {
    await signOut(auth);
    currentUser = null;
  } catch (error) {
    console.error("Sign-out error:", error);
    throw error;
  }
}

export function getCurrentUser() {
  return currentUser;
}

export function setupAuthStateListener(callback) {
  return onAuthStateChanged(auth, (user) => {
    currentUser = user;
    callback(user);
  });
}

// Like functions
export async function addLike(imageFile) {
  if (!currentUser) throw new Error("User not authenticated");

  try {
    await addDoc(collection(db, "likes"), {
      userId: currentUser.uid,
      imageFile: imageFile,
      likedAt: new Date()
    });
  } catch (error) {
    console.error("Error adding like:", error);
    throw error;
  }
}

export async function removeLike(imageFile) {
  if (!currentUser) throw new Error("User not authenticated");

  try {
    const q = query(
      collection(db, "likes"),
      where("userId", "==", currentUser.uid),
      where("imageFile", "==", imageFile)
    );
    const snapshot = await getDocs(q);

    for (const likeDoc of snapshot.docs) {
      await deleteDoc(likeDoc.ref);
    }
  } catch (error) {
    console.error("Error removing like:", error);
    throw error;
  }
}

export async function isImageLiked(imageFile) {
  if (!currentUser) return false;

  try {
    const q = query(
      collection(db, "likes"),
      where("userId", "==", currentUser.uid),
      where("imageFile", "==", imageFile)
    );
    const snapshot = await getDocs(q);
    return snapshot.size > 0;
  } catch (error) {
    console.error("Error checking like:", error);
    return false;
  }
}

// Note functions
export async function addNote(imageFile, text) {
  if (!currentUser) throw new Error("User not authenticated");
  if (!text || text.trim().length === 0) throw new Error("Note cannot be empty");
  if (text.length > 500) throw new Error("Note cannot exceed 500 characters");

  try {
    const docRef = await addDoc(collection(db, "notes"), {
      userId: currentUser.uid,
      imageFile: imageFile,
      text: text.trim(),
      createdAt: new Date(),
      displayName: currentUser.displayName || "Anonymous"
    });
    return docRef.id;
  } catch (error) {
    console.error("Error adding note:", error);
    throw error;
  }
}

export async function getNotes(imageFile) {
  try {
    const q = query(
      collection(db, "notes"),
      where("imageFile", "==", imageFile),
      orderBy("createdAt", "desc")
    );
    const snapshot = await getDocs(q);

    return snapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data(),
      createdAt: doc.data().createdAt?.toDate?.() || new Date()
    }));
  } catch (error) {
    console.error("Error getting notes:", error);
    return [];
  }
}

export async function deleteNote(noteId) {
  if (!currentUser) throw new Error("User not authenticated");

  try {
    const noteDocRef = doc(db, "notes", noteId);
    const noteDocSnap = await getDoc(noteDocRef);

    if (!noteDocSnap.exists()) {
      throw new Error("Note not found");
    }

    if (noteDocSnap.data().userId !== currentUser.uid) {
      throw new Error("Cannot delete note you don't own");
    }

    await deleteDoc(noteDocRef);
  } catch (error) {
    console.error("Error deleting note:", error);
    throw error;
  }
}

// User profile functions
//
// Sort client-side instead of server-side: Firestore requires a composite
// index for `where(userId) + orderBy(ts)`, and these indexes aren't in the
// deployed config. Without the index, the query throws and the profile
// page silently renders empty. The liked/commented sets are small enough
// that in-memory sorting is free.

export async function getUserLikedImages() {
  if (!currentUser) return [];

  const q = query(
    collection(db, "likes"),
    where("userId", "==", currentUser.uid)
  );
  const snapshot = await getDocs(q);

  return snapshot.docs
    .map(doc => ({
      id: doc.id,
      ...doc.data(),
      likedAt: doc.data().likedAt?.toDate?.() || new Date(0)
    }))
    .sort((a, b) => b.likedAt - a.likedAt);
}

export async function getUserCommentedImages() {
  if (!currentUser) return [];

  const q = query(
    collection(db, "notes"),
    where("userId", "==", currentUser.uid)
  );
  const snapshot = await getDocs(q);

  const byFile = new Map();
  for (const doc of snapshot.docs) {
    const data = doc.data();
    const ts = data.createdAt?.toDate?.() || new Date(0);
    const prev = byFile.get(data.imageFile);
    if (!prev || ts > prev) byFile.set(data.imageFile, ts);
  }
  return [...byFile.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([file]) => file);
}
