import { Routes } from '@angular/router';
import { LoginComponent } from './features/auth/login.component';
import { RegisterComponent } from './features/auth/register.component';
import { AuthCallbackComponent } from './features/auth/auth-callback.component';
import { DashboardComponent } from './features/dashboard/dashboard.component';
import { RepositoryComponent } from './features/repositories/repository.component';
import { ChatComponent } from './features/chat/chat.component';

export const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'auth/callback', component: AuthCallbackComponent },
  { path: 'register', component: RegisterComponent },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'repositories/:id', component: RepositoryComponent },
  { path: 'chat', component: ChatComponent },
  { path: '**', redirectTo: 'dashboard' }
];
