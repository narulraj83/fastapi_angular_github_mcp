import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({ providedIn: 'root' })
export class ChatService {
  private http = inject(HttpClient);
  private readonly api = 'http://127.0.0.1:8000/api/v1/chat';

  listSessions() { return this.http.get<any[]>(`${this.api}/sessions`); }
  createSession(repositoryId: number, title = 'New conversation') {
    return this.http.post<any>(`${this.api}/sessions`, { repository_id: repositoryId, session_title: title });
  }
  getSession(id: number) { return this.http.get<any>(`${this.api}/sessions/${id}`); }
  sendMessage(id: number, question: string) {
    return this.http.post<any>(`${this.api}/sessions/${id}/messages`, { question });
  }
  deleteSession(id: number) { return this.http.delete(`${this.api}/${id}`); }
}
