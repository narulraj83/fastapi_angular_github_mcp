import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

export interface Repository {
  id: number; owner: string; repository_name: string; full_name: string;
  description?: string; default_branch: string; visibility: string; html_url: string;
}

@Injectable({ providedIn: 'root' })
export class RepositoryService {
  private http = inject(HttpClient);
  private readonly api = 'http://127.0.0.1:8000/api/v1/repositories';

  list() { return this.http.get<Repository[]>(this.api); }
  connect(owner: string, repo: string) { return this.http.post<Repository>(`${this.api}/connect`, { owner, repo }); }
  tree(id: number) { return this.http.get<any>(`${this.api}/${id}/tree`); }
  readme(id: number) { return this.http.get<any>(`${this.api}/${id}/readme`); }
  branches(id: number) { return this.http.get<any[]>(`${this.api}/${id}/branches`); }
  files(id: number, path = '') {
    return this.http.get<any[] | { result: any[] }>(`${this.api}/${id}/files`, { params: { path } });
  }
  fileContent(id: number, path: string) {
    return this.http.get<any | { result: any }>(`${this.api}/${id}/files/content`, { params: { path } });
  }
}
