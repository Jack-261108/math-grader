import { createRouter, createWebHistory } from 'vue-router';
import MathView from '../views/MathView.vue';
import OmrView from '../views/OmrView.vue';
import WrongBookView from '../views/WrongBookView.vue';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: MathView
  },
  {
    path: '/math',
    name: 'Math',
    component: MathView
  },
  {
    path: '/omr',
    name: 'Omr',
    component: OmrView
  },
  {
    path: '/wrong-book',
    name: 'WrongBook',
    component: WrongBookView
  }
];

export const router = createRouter({
  history: createWebHistory(),
  routes
});
