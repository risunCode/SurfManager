export namespace apps {
	
	export class BackupItem {
	    type: string;
	    path: string;
	    description: string;
	    optional: boolean;
	
	    static createFrom(source: any = {}) {
	        return new BackupItem(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.type = source["type"];
	        this.path = source["path"];
	        this.description = source["description"];
	        this.optional = source["optional"];
	    }
	}
	export class AppPaths {
	    data_paths: string[];
	    exe_paths: string[];
	    reset_folder: string;
	
	    static createFrom(source: any = {}) {
	        return new AppPaths(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.data_paths = source["data_paths"];
	        this.exe_paths = source["exe_paths"];
	        this.reset_folder = source["reset_folder"];
	    }
	}
	export class AppConfig {
	    app_name: string;
	    display_name: string;
	    version: string;
	    active: boolean;
	    description: string;
	    paths: AppPaths;
	    backup_items: BackupItem[];
	    addon_backup_paths: string[];
	
	    static createFrom(source: any = {}) {
	        return new AppConfig(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.app_name = source["app_name"];
	        this.display_name = source["display_name"];
	        this.version = source["version"];
	        this.active = source["active"];
	        this.description = source["description"];
	        this.paths = this.convertValues(source["paths"], AppPaths);
	        this.backup_items = this.convertValues(source["backup_items"], BackupItem);
	        this.addon_backup_paths = source["addon_backup_paths"];
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	

}

export namespace backup {
	
	export class Session {
	    name: string;
	    app: string;
	    size: number;
	    // Go type: time
	    created: any;
	    // Go type: time
	    modified: any;
	    is_active: boolean;
	    is_auto: boolean;
	
	    static createFrom(source: any = {}) {
	        return new Session(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.name = source["name"];
	        this.app = source["app"];
	        this.size = source["size"];
	        this.created = this.convertValues(source["created"], null);
	        this.modified = this.convertValues(source["modified"], null);
	        this.is_active = source["is_active"];
	        this.is_auto = source["is_auto"];
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}

}

export namespace main {
	
	export class Note {
	    id: string;
	    title: string;
	    content: string;
	    created_at: string;
	    updated_at: string;
	
	    static createFrom(source: any = {}) {
	        return new Note(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.title = source["title"];
	        this.content = source["content"];
	        this.created_at = source["created_at"];
	        this.updated_at = source["updated_at"];
	    }
	}

}

