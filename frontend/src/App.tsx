import {Router} from "./Router.tsx";
import {JobProvider} from "./context/JobProvider.tsx";


function App() {
    return (
        <JobProvider><Router/></JobProvider>
    )
}
export default App
