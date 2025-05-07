import {jobContext} from "./jobContext.ts";
import {type PropsWithChildren, useState} from "react";

export const JobProvider = ({children}:PropsWithChildren) => {
    const [job, setJob] = useState(undefined)

    return(
        <jobContext.Provider value={{job, setJob}}>
            {children}
        </jobContext.Provider>
    )
}